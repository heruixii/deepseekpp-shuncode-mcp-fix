# -*- coding: utf-8 -*-
"""
DeepSeek++ ShunCode MCP Fix 3.3.10.33 hash-locked patcher (.32 -> .33)

Evidence: LevelDB snapshot D:\tmp\edsnap-331032-20260916 (session c0ba574e,
20:05-20:14, extension 1.14.0.37). Four loops: two "answered without doing
anything" (02f8e7f5, 1eeb8389: status=complete, totalTools=0), one "stopped
mid-task" (61ad9dfd: generic_continuation_limit_331025 -> error), one that
succeeded only after 7 mcp_discover round-trips (2c7896c5).

Root causes (three layers, all present at once):

A. run_command was never exposed as a direct tool. The adaptive exposure
   picker (background.js _d/Sd/Cd) ranks MCP descriptors purely by keyword
   overlap with the user prompt, and the prompts were "继续" / "A" /
   "继续直到任务完成". dpp_web_response_diag_331015 shows the injected
   ShunCode tools were apply_patch / find_files / get_command_output /
   read_image -- never run_command. The model therefore emitted
   <run_command>...</run_command> exactly as the system prompt instructs,
   the streaming parser has no such target and dropped it as text.
   Proof: turn_diag textChars vs trace visible text: 347->39, 196->0,
   309->0, 223->0, 268->0, 1315->57, 657->17, 790->31 on every failing turn.

B. Capability-handle lifecycle. The .19 temporary alias (id suffix
   dpp331019) is removed only in its own execute() finally. When the model
   consumes the same handle through mcp_invoke directly, the alias survives
   pointing at a consumed handle -> next direct call fails with
   mcp_capability_handle_replayed. A failed transport call also consumes the
   handle. Neither code is in DPP_TRANSPORT_ERROR_CODES_331031, so the loop
   falls into generic nudges and dies at the 3-nudge limit.

C. Completion gate is blind to "zero work done". <task_complete> with
   g.length===0 passes DPP_COMPLETION_GATE_31 unconditionally; the plain
   `final` branch is reached when the text carries unparsed markup but no
   intent phrase (DPP_TOOL_INTENT_331021 -> false).

Fixes:
  A  background.js Cd(): core ShunCode tools get a rank floor
     (run_command 1600, get_command_output/read_files 1000,
     apply_patch/search_files/list_directory 700) so they survive the
     5-slot adaptive cut regardless of prompt wording.
  B1 content.js: retire aliases whose capability was just consumed by any
     mcp_invoke execution (ok or not).
  B2 content.js: handle-lifecycle codes join the transport-failure set;
     steering text tells the model to re-discover then invoke next turn.
  C1 content.js: unregistered tool-tag detector. <name>...</name> where name
     is a known ShunCode tool (or mcp_t_*) but not a registered/aliased tag
     => toolIntent=true, decision unregistered_tool_tag_331033, steering
     explains the tag was ignored and how to reach the tool.
  C2 content.js: <task_complete> with zero tool executions in this loop is
     rejected when reasoning shows tool intent or the prompt is a
     continuation; the loop cannot end `complete` without doing anything.

Usage: python apply-fix331033.py <src_dir> <dst_dir>
Fails closed: any hash or anchor mismatch aborts without writing.
"""
import hashlib, io, os, shutil, sys

EXPECT_SRC = {
    "manifest.json":                 "4c30ebaf146b0adaeb13630c5ce5dd764019d9a6445666a90547896941614756",
    "content-scripts/content.js":    "c668d465e6ec32a2ce976e2346dfb2f603bed64d9e1b4ac790918afad7db1713",
    "content-scripts/main-world.js": "b2f037ef00701bd9f4d7abd6745265d61af396ffb876c3e0aa25f2356f09714b",
    "background.js":                 "7d4bccc629b9a0d4c645f86b4ca3005ef4f8d771a655b11189761b4c9c2a850f",
    "fix3-policy.js":                "dea99bc86f34b4692df88ce1bd4ac614390bf75cb51712c85e633e1c7927ef1d",
}


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def sub_once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit("FAIL-CLOSED: anchor %s found %d times (expected 1)" % (label, n))
    return s.replace(old, new, 1)


# =============================== background.js ==============================
# Fix A: rank floor for core ShunCode tools inside the adaptive picker.
CD_OLD = ("function Cd(e,t,n,r){let i=Td(`${e.name} ${e.invocationName}`),a=Td(e.title),"
          "o=Td(e.description),s=r?1e4:0;")
CD_NEW = ("function DPP_CORE_TOOL_FLOOR_331033(e){let t=String(e?.invocationName??e?.name??``)"
          ".toLowerCase();return/(?:^|_)run_command$/.test(t)?1600:"
          "/(?:^|_)(?:get_command_output|read_files)$/.test(t)?1e3:"
          "/(?:^|_)(?:apply_patch|search_files|list_directory)$/.test(t)?700:0}"
          "function Cd(e,t,n,r){let i=Td(`${e.name} ${e.invocationName}`),a=Td(e.title),"
          "o=Td(e.description),s=(r?1e4:0)+DPP_CORE_TOOL_FLOOR_331033(e);")

# =============================== content.js =================================
# Fix B2: handle-lifecycle codes are non-progress just like transport codes.
CODES_OLD = ("var DPP_TRANSPORT_ERROR_CODES_331031=new Set([`mcp_network_error`,`mcp_timeout`,"
             "`mcp_unauthorized`,`mcp_server_error`,`capability_expired`,`capability_not_found`,"
             "`bridge_unavailable`]);")
CODES_NEW = ("var DPP_TRANSPORT_ERROR_CODES_331031=new Set([`mcp_network_error`,`mcp_timeout`,"
             "`mcp_unauthorized`,`mcp_server_error`,`capability_expired`,`capability_not_found`,"
             "`bridge_unavailable`,`mcp_transport_timeout`,`mcp_capability_handle_replayed`,"
             "`mcp_capability_handle_expired`,`mcp_capability_handle_invalid`,"
             "`mcp_capability_descriptor_stale`]);"
             "var DPP_HANDLE_ERROR_CODES_331033=new Set([`mcp_capability_handle_replayed`,"
             "`mcp_capability_handle_expired`,`mcp_capability_handle_invalid`,"
             "`mcp_capability_descriptor_stale`,`capability_expired`,`capability_not_found`]);"
             "function DPP_STEP_TRANSPORT_CODE_331033(e){let t=``;for(let n of Array.isArray(e)?e:[])"
             "DPP_IS_TRANSPORT_FAILURE_331031(n)&&(t=String(n?.result?.error?.code??``));return t}"
             "var DPP_SHUNCODE_TOOL_TAGS_331033=new Set([`run_command`,`get_command_output`,"
             "`send_command_input`,`cancel_command`,`read_files`,`read_image`,`find_files`,"
             "`search_files`,`list_directory`,`apply_patch`,`get_diagnostics`,`lsp`,`set_todos`,"
             "`update_plan`,`report_progress`]);"
             "function DPP_UNREGISTERED_TOOL_TAG_331033(e,t){let n=String(e??``);if(!n||n.length>2e5)return``;"
             "let r=/<([a-z][a-z0-9_]{2,96})>[\\s\\S]{0,20000}?<\\/\\1>/gi,i;while(i=r.exec(n)){let e=i[1].toLowerCase(),"
             "n=e.replace(/^mcp_t_[a-z0-9]+(?:_[a-z0-9]+){4}_/,``);"
             "if(typeof t==`function`?t(e):t&&typeof t.has==`function`&&t.has(e))continue;"
             "if(DPP_SHUNCODE_TOOL_TAGS_331033.has(n)||/^mcp_t_/.test(e))return e}return``}"
             "function DPP_UNREGISTERED_TAG_STEERING_331033(e,t){return String(e??``).toLowerCase().startsWith(`zh`)?"
             "`[Fix 3.3.10.33 \\u672a\\u6ce8\\u518c\\u5de5\\u5177\\u6807\\u7b7e] \\u4f60\\u4e0a\\u4e00\\u8f6e\\u8f93\\u51fa\\u7684 <${t}> "
             "\\u4e0d\\u662f\\u5f53\\u524d\\u53ef\\u7528\\u7684\\u5de5\\u5177\\u6807\\u7b7e\\uff0c\\u5df2\\u88ab\\u5ffd\\u7565\\u3001\\u672a\\u6267\\u884c\\uff0c"
             "\\u4efb\\u52a1\\u6ca1\\u6709\\u63a8\\u8fdb\\u3002\\u8be5\\u5de5\\u5177\\u9700\\u8981\\u5148\\u7528 <mcp_discover>{\"query\":\"${t}\"}</mcp_discover> "
             "\\u83b7\\u53d6 capability\\uff0c\\u7136\\u540e\\u5728\\u4e0b\\u4e00\\u8f6e\\u7acb\\u5373\\u7528 mcp_invoke \\u6267\\u884c\\u3002"
             "\\u4e0d\\u8981\\u518d\\u76f4\\u63a5\\u8f93\\u51fa <${t}> \\u6807\\u7b7e\\u3002`:"
             "`[Fix 3.3.10.33 unregistered tool tag] Your previous turn emitted <${t}>, which is not an available tool tag; "
             "it was ignored and nothing executed. Reach that tool via <mcp_discover>{\"query\":\"${t}\"}</mcp_discover> first, "
             "then call mcp_invoke with the returned capability in the very next turn. Do not emit <${t}> directly again.`}"
             "function DPP_ZERO_TOOL_COMPLETE_BLOCK_331033(e,t,n){if(Array.isArray(e)&&e.length>0)return``;"
             "let r=String(n??``).trim(),i=/^(?:\\u7ee7\\u7eed|\\u63a5\\u7740|continue|resume|go\\s+on)/i.test(r)||"
             "/\\u7ee7\\u7eed.*(?:\\u76f4\\u5230|\\u5230).*\\u5b8c\\u6210|until.*(?:complete|done)/i.test(r);"
             "if(!i&&!DPP_TOOL_INTENT_TEXT_331021(String(t??``)))return``;"
             "return`<task_complete> was declared but this run executed zero tools. A continuation or a tool-announcing plan cannot "
             "be completed without doing the work. Execute the required tool call now; if the task truly needs no tool, answer plainly "
             "without <task_complete>.`}")

# Fix B2 (steering text): mention handle codes.
TSTEER_OLD = "function DPP_TRANSPORT_STEERING_331031(e,t){return String(e??``).toLowerCase().startsWith(`zh`)?"
TSTEER_NEW = ("function DPP_TRANSPORT_STEERING_331031(e,t,n){if(DPP_HANDLE_ERROR_CODES_331033.has(String(n??``)))"
              "return String(e??``).toLowerCase().startsWith(`zh`)?"
              "`[Fix 3.3.10.33 \\u80fd\\u529b\\u53e5\\u67c4\\u5931\\u6548] \\u4e0a\\u4e00\\u6b65\\u7684\\u5de5\\u5177\\u8c03\\u7528\\u56e0 ${n} "
              "\\u672a\\u6267\\u884c\\uff08\\u7b2c ${t} \\u6b21\\uff09\\uff0c\\u4efb\\u52a1\\u6ca1\\u6709\\u5b8c\\u6210\\u3002capability \\u53e5\\u67c4\\u662f"
              "\\u4e00\\u6b21\\u6027\\u7684\\uff1a\\u73b0\\u5728\\u91cd\\u65b0 <mcp_discover>\\uff0c\\u5e76\\u5728\\u4e0b\\u4e00\\u8f6e\\u7acb\\u5373\\u7528"
              "\\u65b0\\u53e5\\u67c4 mcp_invoke\\u3002\\u4e0d\\u8981\\u53ea\\u7528\\u6587\\u5b57\\u56de\\u590d\\u3002`:"
              "`[Fix 3.3.10.33 capability handle lost] The previous tool call did not execute (${n}, attempt ${t}). The task is NOT complete. "
              "Capability handles are single-use: call mcp_discover again now and mcp_invoke with the fresh handle in the very next turn. "
              "Do not reply with text only.`;"
              "return String(e??``).toLowerCase().startsWith(`zh`)?")

# Fix B1: retire aliases when any mcp_invoke execution completes.
ALIAS_OLD = "_.push(DPPExecution),DPPInstallAliases331019(DPPExecution),n(`AGENT_TOOL_COMPLETE`"
ALIAS_NEW = ("_.push(DPPExecution),(()=>{try{if(String(e.toolName??``).toLowerCase().endsWith(`mcp_invoke`)){"
             "let t=r?.args?.capability;if(typeof t==`string`)for(let[e,n]of[...DPPAliases331019.entries()])"
             "n?.capability===t&&DPPRemoveAlias331019(e,t)}}catch{}})(),"
             "DPPInstallAliases331019(DPPExecution),n(`AGENT_TOOL_COMPLETE`")

# Track the failing code per step.
TCODE_OLD = ("y.lastStepHadTransportFailure=DPP_STEP_TRANSPORT_FAILURES_331031(_)>0,"
             "y.lastStepHadTransportFailure?y.transportFailuresInStep+=1:y.transportFailuresInStep=0,")
TCODE_NEW = ("y.lastStepHadTransportFailure=DPP_STEP_TRANSPORT_FAILURES_331031(_)>0,"
             "y.lastTransportCode=y.lastStepHadTransportFailure?DPP_STEP_TRANSPORT_CODE_331033(_):``,"
             "y.lastStepHadTransportFailure?y.transportFailuresInStep+=1:y.transportFailuresInStep=0,")
TUSE_OLD = "return y.completionReason=DPP_TRANSPORT_STEERING_331031(d,y.transportFailuresInStep),q(`tool_transport_failure_331031`,!1)}"
TUSE_NEW = "return y.completionReason=DPP_TRANSPORT_STEERING_331031(d,y.transportFailuresInStep,y.lastTransportCode),q(`tool_transport_failure_331031`,!1)}"

# Fix C1: unregistered tag => tool intent, in both decision and steering.
K_OLD = ("shouldStopAfterTurn:({message:e})=>{ce=Yz(e),le=e.content.some(e=>e.type===`toolCall`);"
         "let n=ce,r=le,k=DPP_TOOL_INTENT_331021(n,te),")
K_NEW = ("shouldStopAfterTurn:({message:e})=>{ce=Yz(e),le=e.content.some(e=>e.type===`toolCall`);"
         "let n=ce,r=le,DPPUnregTag331033=r?``:DPP_UNREGISTERED_TOOL_TAG_331033(n,e=>v.has(e)||DPPAliases331019.has(e)),"
         "k=!!DPPUnregTag331033||DPP_TOOL_INTENT_331021(n,te);y.unregisteredTag=DPPUnregTag331033;"
         "DPPUnregTag331033&&DPP_RECORD_AGENT_TURN_DIAG_331021({stage:`unregistered_tool_tag_331033`,loopId:a,chatSessionId:s,"
         "stepIndex:b,turnIndex:ue,responseMessageId:h(),textChars:n.length,reasoningChars:te.length,hasToolCall:!1,toolIntent:!0,"
         "decision:`unregistered_tool_tag_331033`,errorMessage:DPPUnregTag331033});")
KS_OLD = "getSteeringMessages:async()=>{let e=DPP_TOOL_INTENT_331021(ce,te),"
KS_NEW = "getSteeringMessages:async()=>{let e=!!y.unregisteredTag||DPP_TOOL_INTENT_331021(ce,te),"
# prepend the tag hint to the tool-intent steering message
KP_OLD = "i=DPP_TOOL_INTENT_STEERING_331021(t.originalPrompt,y.lastAssistantText,g,y.toolIntentNudgesInStep,d),"
KP_NEW = ("i=DPP_TOOL_INTENT_STEERING_331021(t.originalPrompt,y.lastAssistantText,g,y.toolIntentNudgesInStep,d),"
          "y.unregisteredTag&&(i=`${DPP_UNREGISTERED_TAG_STEERING_331033(d,y.unregisteredTag)}\\n\\n${i}`),")

# Fix C2: zero-tool task_complete is not a completion.
GATE_OLD = "let i=Sz(n);if(i){let e=DPP_COMPLETION_GATE_31(g);if(e.ok)return y.completionReason=``,ie=n,q(`task_complete`,!0);"
GATE_NEW = ("let i=Sz(n);if(i){let e=DPP_COMPLETION_GATE_31(g),DPPZeroBlock331033=e.ok?DPP_ZERO_TOOL_COMPLETE_BLOCK_331033(g,te,t.originalPrompt):``;"
            "if(DPPZeroBlock331033){if(y.completionReason=DPPZeroBlock331033,y.currentTurnIsNudge&&y.count>=Ce.maxNudges)"
            "return oe=!0,se=DPPZeroBlock331033,q(`zero_tool_complete_limit_331033`,!0);return q(`zero_tool_complete_331033`,!1)}"
            "if(e.ok)return y.completionReason=``,ie=n,q(`task_complete`,!0);")

# y state init
Y_OLD = "transportFailuresInStep:0,lastStepHadTransportFailure:!1}"
Y_NEW = "transportFailuresInStep:0,lastStepHadTransportFailure:!1,lastTransportCode:``,unregisteredTag:``}"

# ---------------- release-chain maintenance ----------------
VERSION_GATE_OLD = "'1.14.0.35','1.14.0.36','1.14.0.37'"
VERSION_GATE_NEW = "'1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38'"
VNAME_GATE_OLD = "'1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32'"
VNAME_GATE_NEW = "'1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33'"
VNAME_RE_OLD = "|30|31|32)$"
VNAME_RE_NEW = "|30|31|32|33)$"
LOCALE_OLD = "DeepSeek++ ShunCode MCP Fix 3.3.10.32"
LOCALE_NEW = "DeepSeek++ ShunCode MCP Fix 3.3.10.33"


def bump_release_chain(dst):
    changed = []
    for fn in sorted(os.listdir(dst)):
        if not (fn.startswith("fix") and fn.endswith(".js") and "selftest" in fn):
            continue
        if fn.startswith("fix331033"):
            continue
        fp = os.path.join(dst, fn)
        s = read(fp)
        out = s
        if VERSION_GATE_OLD in out:
            out = out.replace(VERSION_GATE_OLD, VERSION_GATE_NEW)
        if VNAME_GATE_OLD in out:
            out = out.replace(VNAME_GATE_OLD, VNAME_GATE_NEW)
        if VNAME_RE_OLD in out:
            out = out.replace(VNAME_RE_OLD, VNAME_RE_NEW)
        out = out.replace("mf.version==='1.14.0.37'", "mf.version==='1.14.0.38'")
        out = out.replace('manifest.version === "1.14.0.37"', 'manifest.version === "1.14.0.38"')
        out = out.replace('"manifest version is 1.14.0.37"', '"manifest version is 1.14.0.38"')
        out = out.replace('manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.32"',
                          'manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.33"')
        out = out.replace('"manifest version_name is Fix 3.3.10.32"', '"manifest version_name is Fix 3.3.10.33"')
        out = out.replace("mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.32'",
                          "mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.33'")
        if out != s:
            write(fp, out)
            changed.append(fn)
    for rel in ("_locales/en/messages.json", "_locales/zh_CN/messages.json"):
        fp = os.path.join(dst, rel.replace("/", os.sep))
        s = read(fp)
        if LOCALE_OLD in s:
            write(fp, s.replace(LOCALE_OLD, LOCALE_NEW))
            changed.append(rel)
    return changed


def patch_content(s):
    s = sub_once(s, CODES_OLD, CODES_NEW, "transport-codes+helpers")
    s = sub_once(s, TSTEER_OLD, TSTEER_NEW, "transport-steering-handle")
    s = sub_once(s, ALIAS_OLD, ALIAS_NEW, "alias-retire-on-invoke")
    s = sub_once(s, TCODE_OLD, TCODE_NEW, "track-transport-code")
    s = sub_once(s, TUSE_OLD, TUSE_NEW, "use-transport-code")
    s = sub_once(s, K_OLD, K_NEW, "unregistered-tag-decision")
    s = sub_once(s, KS_OLD, KS_NEW, "unregistered-tag-steering-mode")
    s = sub_once(s, KP_OLD, KP_NEW, "unregistered-tag-steering-text")
    s = sub_once(s, GATE_OLD, GATE_NEW, "zero-tool-complete-gate")
    s = sub_once(s, Y_OLD, Y_NEW, "loop-state-init")
    return s


def patch_background(s):
    return sub_once(s, CD_OLD, CD_NEW, "core-tool-floor")


def patch_manifest(s):
    s = sub_once(s, '"version": "1.14.0.37"', '"version": "1.14.0.38"', "manifest-version")
    s = sub_once(s, '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.32"',
                    '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.33"', "manifest-version-name")
    return s


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply-fix331033.py <src_dir> <dst_dir>")
    src, dst = sys.argv[1], sys.argv[2]
    for rel, want in EXPECT_SRC.items():
        p = os.path.join(src, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            raise SystemExit("FAIL-CLOSED: missing %s" % rel)
        got = sha(p)
        if got != want:
            raise SystemExit("FAIL-CLOSED: %s sha mismatch\n  expected %s\n  got      %s" % (rel, want, got))
    print("source hash-lock OK (5/5)")
    # dry-run all anchors against source before touching dst
    patch_content(read(os.path.join(src, "content-scripts", "content.js")))
    patch_background(read(os.path.join(src, "background.js")))
    patch_manifest(read(os.path.join(src, "manifest.json")))
    print("anchor dry-run OK")
    if os.path.abspath(src) != os.path.abspath(dst):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    cjs = os.path.join(dst, "content-scripts", "content.js")
    write(cjs, patch_content(read(cjs)))
    bg = os.path.join(dst, "background.js")
    write(bg, patch_background(read(bg)))
    mf = os.path.join(dst, "manifest.json")
    write(mf, patch_manifest(read(mf)))
    print("patched content.js + background.js + manifest.json")
    here = os.path.dirname(os.path.abspath(__file__))
    suite = os.path.join(here, "fix331033-capability-exposure-selftest.js")
    if os.path.isfile(suite):
        shutil.copyfile(suite, os.path.join(dst, "fix331033-capability-exposure-selftest.js"))
        print("installed fix331033 selftest")
    ch = bump_release_chain(dst)
    print("release chain bumped in %d files" % len(ch))


if __name__ == "__main__":
    main()

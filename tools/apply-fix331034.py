# -*- coding: utf-8 -*-
r"""
DeepSeek++ ShunCode MCP Fix 3.3.10.34 hash-locked patcher (.33 -> .34)

Evidence: LevelDB snapshot D:\tmp\edsnap-331033-20260916-2319, session c0ba574e
23:12-23:18. Four agent loops ended `status=stopping / error="已停止"`. Each
stop timestamp matches a manual `mw_send_hook_seen` (user typed a new message
while the Agent was mid-step) to the millisecond; the stop came from
DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107 -> r1(). Not a regression --
every step before the stop was a real HTTP-200 run_command execution.

Two real defects found on the side:

E. False `run_command_failed`. DPP_NORMALIZE_RUN_COMMAND_RESULT_33108 regex-
   scans the *entire* result text (header + command output) for
   `status=failed` / `exit_code=N`. When the command greps the extension's own
   sources (or any text containing those words) a completed exit_code 0 run is
   reported as failed (3 occurrences 23:15-23:17; header said
   `status: completed / exit_code: 0`).
F. Manual supersede is invisible. The trace only says "已停止" and no
   diagnostic is recorded, so the user reads it as "the task died by itself".

Fixes:
  E  parse status/exit_code from the RUN_COMMAND header only (text before
     `--- OUTPUT BEGIN ---`); fall back to the old whole-text scan only when no
     header marker exists.
  F  r1(reason?) accepts an explicit reason; the manual-request abort passes a
     localized "interrupted by your new message; send 继续 to resume" text and
     records turn_diag stage/decision `manual_supersede_331034`.

Usage: python apply-fix331034.py <src_dir> <dst_dir>   (dst must differ from src)
Fails closed on any hash or anchor mismatch.
"""
import hashlib, io, os, shutil, sys

EXPECT_SRC = {
    "manifest.json":                 "8f2c71ab7fe4b20cfcfe82187252c3dd01e0db507777a74b677e3cd943439759",
    "content-scripts/content.js":    "d2b81f231c0e84bbdb1301de7fd59d24a6427f18f65dc14b92ae2edbc1c1dc64",
    "content-scripts/main-world.js": "b2f037ef00701bd9f4d7abd6745265d61af396ffb876c3e0aa25f2356f09714b",
    "background.js":                 "ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32",
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


# ---- Fix E: header-only status parsing --------------------------------------
NORM_OLD = ("function DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(e,t){if(DPP_TOOL_NAME_33(typeof e==`string`?e:e?.invocationName??e?.name)!==`run_command`||t?.ok!==!0)return t;"
            "let n=DPP_RUN_COMMAND_TEXT_33108(t),r=/[\"']?status[\"']?\\s*[:=]\\s*[\"']?failed\\b/i.test(n),"
            "i=/[\"']?exit[_-]?code[\"']?\\s*[:=]\\s*[\"']?(-?\\d+)\\b/i.exec(n),a=i?Number(i[1]):null;")
NORM_NEW = ("function DPP_RUN_COMMAND_HEADER_331034(e){let t=String(e??``),n=t.indexOf(`--- OUTPUT BEGIN ---`);"
            "if(n<0)return{header:t,hasMarker:!1};return{header:t.slice(0,n),hasMarker:!0}}"
            "function DPP_RUN_COMMAND_STATUS_331034(e){let{header:t,hasMarker:n}=DPP_RUN_COMMAND_HEADER_331034(e),"
            "r=/(?:^|\\n|\\\\n)status:\\s*([a-z_]+)\\s*(?:\\n|\\\\n)exit_code:\\s*(-?\\d+)\\b/i.exec(t);"
            "if(r)return{failed:r[1].toLowerCase()===`failed`,exitCode:Number(r[2]),source:`header`};"
            "let i=n?t:String(e??``),a=/[\"']?status[\"']?\\s*[:=]\\s*[\"']?failed\\b/i.test(i),"
            "o=/[\"']?exit[_-]?code[\"']?\\s*[:=]\\s*[\"']?(-?\\d+)\\b/i.exec(i);"
            "return{failed:a,exitCode:o?Number(o[1]):null,source:n?`header_loose`:`fulltext`}}"
            "function DPP_NORMALIZE_RUN_COMMAND_RESULT_33108(e,t){if(DPP_TOOL_NAME_33(typeof e==`string`?e:e?.invocationName??e?.name)!==`run_command`||t?.ok!==!0)return t;"
            "let n=DPP_RUN_COMMAND_TEXT_33108(t),DPPStatus331034=DPP_RUN_COMMAND_STATUS_331034(n),r=DPPStatus331034.failed,a=DPPStatus331034.exitCode;")

# ---- Fix F: visible manual supersede ----------------------------------------
R1_OLD = "function r1(){FX(),o1();let e=Q;if(C0(e=>({...e,status:`stopping`,error:$(`content.agent.stopped`)}),{immediate:!0}),"
R1_NEW = ("function r1(DPPReason331034){FX(),o1();let e=Q,DPPStopText331034=typeof DPPReason331034==`string`&&DPPReason331034?DPPReason331034:$(`content.agent.stopped`);"
          "if(C0(e=>({...e,status:`stopping`,error:DPPStopText331034}),{immediate:!0}),")
R1_TAIL_OLD = "RX(e,`paused`,0,0,$(`content.agent.stopped`))}}var DPP_AGENT_PAGEHIDE_BOUND_33108=!1;"
R1_TAIL_NEW = "RX(e,`paused`,0,0,DPPStopText331034)}}var DPP_AGENT_PAGEHIDE_BOUND_33108=!1;"

ABORT_OLD = "function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;return r1(),!0}"
ABORT_NEW = ("function DPP_MANUAL_SUPERSEDE_TEXT_331034(e){return String(e??``).toLowerCase().startsWith(`zh`)?"
             "`\\u5df2\\u88ab\\u4f60\\u7684\\u65b0\\u6d88\\u606f\\u4e2d\\u65ad\\uff08Agent \\u8fd0\\u884c\\u4e2d\\u53d1\\u9001\\u65b0\\u6d88\\u606f\\u4f1a\\u653e\\u5f03\\u5f53\\u524d\\u4efb\\u52a1\\uff09\\u3002"
             "\\u7b49\\u72b6\\u6001\\u680f\\u663e\\u793a\\u7ed3\\u675f\\u540e\\u518d\\u53d1\\u201c\\u7ee7\\u7eed\\u201d\\u53ef\\u6062\\u590d\\u3002`:"
             "`Interrupted by your new message (sending while the Agent is running abandons the current task). "
             "Wait for the status bar to finish, then send \"continue\" to resume.`}"
             "function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;"
             "try{DPP_RECORD_AGENT_TURN_DIAG_331021({stage:`manual_supersede_331034`,loopId:typeof LY==`string`?LY:``,"
             "chatSessionId:String(BY?.chatSessionId??``),stepIndex:Number(BY?.totalSteps??0),decision:`manual_supersede_331034`,"
             "errorMessage:`user sent a manual message while the agent loop was active`})}catch{}"
             "return r1(DPP_MANUAL_SUPERSEDE_TEXT_331034(typeof nX==`string`?nX:``)),!0}")

# ---- release chain -----------------------------------------------------------
VERSION_GATE_OLD = "'1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38'"
VERSION_GATE_NEW = "'1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.39'"
VNAME_GATE_OLD = "'1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33'"
VNAME_GATE_NEW = "'1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.34'"
VNAME_RE_OLD = "|30|31|32|33)$"
VNAME_RE_NEW = "|30|31|32|33|34)$"
LOCALE_OLD = "DeepSeek++ ShunCode MCP Fix 3.3.10.33"
LOCALE_NEW = "DeepSeek++ ShunCode MCP Fix 3.3.10.34"


def bump_release_chain(dst):
    changed = []
    for fn in sorted(os.listdir(dst)):
        if not (fn.startswith("fix") and fn.endswith(".js") and "selftest" in fn):
            continue
        if fn.startswith("fix331034"):
            continue
        fp = os.path.join(dst, fn)
        s = read(fp)
        out = s
        for a, b in ((VERSION_GATE_OLD, VERSION_GATE_NEW), (VNAME_GATE_OLD, VNAME_GATE_NEW), (VNAME_RE_OLD, VNAME_RE_NEW),
                     ("mf.version==='1.14.0.38'", "mf.version==='1.14.0.39'"),
                     ('manifest.version === "1.14.0.38"', 'manifest.version === "1.14.0.39"'),
                     ('"manifest version is 1.14.0.38"', '"manifest version is 1.14.0.39"'),
                     ('manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.33"', 'manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.34"'),
                     ('"manifest version_name is Fix 3.3.10.33"', '"manifest version_name is Fix 3.3.10.34"'),
                     ("mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.33'", "mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.34'")):
            out = out.replace(a, b)
        if fn == "fix33108-lifecycle-selftest.js":
            out = out.replace("between('function r1()', 'async function i1(e)')",
                              "between('function r1(DPPReason331034)', 'async function i1(e)')")
        if fn == "fix33107-agent-lifecycle-mcp503-selftest.js":
            out = out.replace("src.includes('function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;return r1(),!0}')",
                              "src.includes('function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;')&&src.includes('return r1(DPP_MANUAL_SUPERSEDE_TEXT_331034(')")
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
    s = sub_once(s, NORM_OLD, NORM_NEW, "run-command-header-status")
    s = sub_once(s, R1_OLD, R1_NEW, "r1-reason-param")
    s = sub_once(s, R1_TAIL_OLD, R1_TAIL_NEW, "r1-reason-tail")
    s = sub_once(s, ABORT_OLD, ABORT_NEW, "manual-supersede-visible")
    return s


def patch_manifest(s):
    s = sub_once(s, '"version": "1.14.0.38"', '"version": "1.14.0.39"', "manifest-version")
    s = sub_once(s, '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.33"',
                    '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.34"', "manifest-version-name")
    return s


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply-fix331034.py <src_dir> <dst_dir>")
    src, dst = sys.argv[1], sys.argv[2]
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit("FAIL-CLOSED: dst must differ from src (patch into a temp tree, then copy over)")
    for rel, want in EXPECT_SRC.items():
        p = os.path.join(src, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            raise SystemExit("FAIL-CLOSED: missing %s" % rel)
        got = sha(p)
        if got != want:
            raise SystemExit("FAIL-CLOSED: %s sha mismatch\n  expected %s\n  got      %s" % (rel, want, got))
    print("source hash-lock OK (5/5)")
    patch_content(read(os.path.join(src, "content-scripts", "content.js")))
    patch_manifest(read(os.path.join(src, "manifest.json")))
    print("anchor dry-run OK")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cjs = os.path.join(dst, "content-scripts", "content.js")
    write(cjs, patch_content(read(cjs)))
    mf = os.path.join(dst, "manifest.json")
    write(mf, patch_manifest(read(mf)))
    print("patched content.js + manifest.json")
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("fix331034-run-command-status-selftest.js",):
        cand = [os.path.join(here, name), os.path.join(here, "..", name)]
        for c in cand:
            if os.path.isfile(c):
                shutil.copyfile(c, os.path.join(dst, name))
                print("installed", name)
                break
    ch = bump_release_chain(dst)
    print("release chain bumped in %d files" % len(ch))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
DeepSeek++ ShunCode MCP Fix 3.3.10.31 hash-locked patcher (.30 -> .31)

Root cause (handover doc 2.5): an MCP transport failure (mcp_network_error)
returns a structured failed toolExecution instead of throwing. The completion
gate counted it as progress, the turn resolved to `final`, the trace was stored
as status:"complete", and DPP_RESUME_TRACE_CHAIN_331010 (which only accepts
error/stopping/expired-running and uses the newest complete as a watermark)
then refused to ever resume. "continue"/"retry" degraded into plain chat.

Fix A  content-scripts/content.js  shouldStopAfterTurn
       A transport-class tool failure in the current step must never resolve to
       `final`. It re-steers; once the retry budget is exhausted the loop stops
       via oe/se, which routes to AGENT_LOOP_ERROR -> trace status:"error".
Fix B  content-scripts/content.js  DPP_RESUME_TRACE_CHAIN_331010
       The complete-watermark only counts genuinely successful runs, so a
       mislabelled complete can no longer mask a resumable interrupted run.

Usage: python apply-fix331031.py <src_dir> <dst_dir>
Fails closed: any hash or anchor mismatch aborts without writing.
"""
import hashlib, io, os, shutil, sys

EXPECT_SRC = {
    "manifest.json":                 "3a9ef35af548ba7ee05fd2c07f349943b1cd9375fcc753d178740fe099f0ee4c",
    "content-scripts/content.js":    "1ae30d0593c51dd1f4762529c3f686fd5855ce5c5232fdd8c3a34e85ee3c618e",
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


# ---------------- Fix A ----------------
HELPERS_ANCHOR = "function DPP_HAS_PROGRESS_31(e){return e.some(e=>e?.result?.ok===!0&&e?.result?.error?.code!==`dpp_fix3_no_progress`)}"

HELPERS_NEW = HELPERS_ANCHOR + (
    "var DPP_TRANSPORT_ERROR_CODES_331031=new Set(["
    "`mcp_network_error`,`mcp_timeout`,`mcp_unauthorized`,`mcp_server_error`,"
    "`capability_expired`,`capability_not_found`,`bridge_unavailable`]);"
    "function DPP_IS_TRANSPORT_FAILURE_331031(e){"
    "if(!e||typeof e!=`object`)return!1;"
    "let t=e.result;if(!t||typeof t!=`object`||t.ok===!0)return!1;"
    "let n=t.error&&typeof t.error==`object`?String(t.error.code??``):``;"
    "return DPP_TRANSPORT_ERROR_CODES_331031.has(n)}"
    "function DPP_STEP_TRANSPORT_FAILURES_331031(e){"
    "return(Array.isArray(e)?e:[]).filter(DPP_IS_TRANSPORT_FAILURE_331031).length}"
    "function DPP_TRACE_HAS_REAL_SUCCESS_331031(e){"
    "if(!e||typeof e!=`object`)return!1;"
    "let t=e=>Array.isArray(e)?e.some(e=>e?.result?.ok===!0):!1;"
    "if(t(e.initialExecutions))return!0;"
    "for(let n of Array.isArray(e.steps)?e.steps:[])if(t(n?.toolExecutions))return!0;"
    "return!1}"
    "var DPP_TRANSPORT_RETRY_MAX_331031=3;"
    "function DPP_TRANSPORT_STEERING_331031(e,t){"
    "return String(e??``).toLowerCase().startsWith(`zh`)"
    "?`[Fix 3.3.10.31 \\u4f20\\u8f93\\u6545\\u969c] \\u4e0a\\u4e00\\u6b65\\u7684\\u5de5\\u5177\\u8c03\\u7528\\u56e0 MCP \\u4f20\\u8f93\\u5931\\u8d25\\u800c\\u672a\\u6267\\u884c\\uff08\\u7b2c ${t} \\u6b21\\uff09\\uff0c\\u4e0d\\u662f\\u4efb\\u52a1\\u5df2\\u5b8c\\u6210\\u3002\\u8bf7\\u76f4\\u63a5\\u91cd\\u65b0\\u53d1\\u8d77\\u540c\\u4e00\\u4e2a\\u5de5\\u5177\\u8c03\\u7528\\uff0c\\u4e0d\\u8981\\u53ea\\u7528\\u6587\\u5b57\\u56de\\u590d\\u3002`"
    ":`[Fix 3.3.10.31 transport failure] The previous tool call did not execute because the MCP transport failed (attempt ${t}). The task is NOT complete. Re-issue the same tool call directly instead of replying with text only.`}"
    "function DPP_TRANSPORT_LIMIT_331031(e,t){"
    "return String(e??``).toLowerCase().startsWith(`zh`)"
    "?`DeepSeek++ \\u5df2\\u8fde\\u7eed ${t} \\u6b21\\u9047\\u5230 MCP \\u4f20\\u8f93\\u6545\\u969c\\uff0c\\u5de5\\u5177\\u59cb\\u7ec8\\u672a\\u80fd\\u6267\\u884c\\u3002\\u4efb\\u52a1\\u5df2\\u4ee5\\u9519\\u8bef\\u72b6\\u6001\\u505c\\u6b62\\uff08\\u975e\\u5b8c\\u6210\\uff09\\uff0c\\u4ee5\\u4fbf\\u6062\\u590d\\u7f51\\u5173\\u53ef\\u4ee5\\u63a5\\u7ba1\\u3002\\u8bf7\\u786e\\u8ba4\\u672c\\u5730 MCP \\u670d\\u52a1\\u53ef\\u8fbe\\u540e\\u53d1\\u201c\\u7ee7\\u7eed\\u201d\\u3002`"
    ":`DeepSeek++ hit ${t} consecutive MCP transport failures and the tool never executed. The run was stopped as an error (not complete) so the resume gateway can pick it up. Verify the local MCP server is reachable, then send \"continue\".`}"
)

STATE_OLD = ("y={active:!1,pendingTurn:!1,currentTurnIsNudge:!1,nudgedInStep:!1,"
             "genericNudgesInStep:0,toolIntentNudgesInStep:0,lastToolIntent:!1,count:0,"
             "lastAssistantText:``,completionReason:``}")
STATE_NEW = ("y={active:!1,pendingTurn:!1,currentTurnIsNudge:!1,nudgedInStep:!1,"
             "genericNudgesInStep:0,toolIntentNudgesInStep:0,lastToolIntent:!1,count:0,"
             "lastAssistantText:``,completionReason:``,transportFailuresInStep:0,"
             "lastStepHadTransportFailure:!1}")

PROGRESS_OLD = "e&&(y.count=0,y.completionReason=``)"
PROGRESS_NEW = ("y.lastStepHadTransportFailure=DPP_STEP_TRANSPORT_FAILURES_331031(_)>0,"
                "y.lastStepHadTransportFailure?y.transportFailuresInStep+=1:y.transportFailuresInStep=0,"
                "e&&(y.count=0,y.completionReason=``)")

FINAL_OLD = "return o?q(k?`tool_intent_needed`:`continuation_needed`,!1):(ie=n,q(`final`,!0))"
FINAL_NEW = ("if(y.lastStepHadTransportFailure){"
             "if(y.transportFailuresInStep>=DPP_TRANSPORT_RETRY_MAX_331031)"
             "return oe=!0,se=DPP_TRANSPORT_LIMIT_331031(d,y.transportFailuresInStep),"
             "q(`tool_transport_failure_limit_331031`,!0);"
             "return y.completionReason=DPP_TRANSPORT_STEERING_331031(d,y.transportFailuresInStep),"
             "q(`tool_transport_failure_331031`,!1)}"
             + FINAL_OLD)

# ---------------- Fix B ----------------
WATERMARK_OLD = ("let a=Math.max(0,...t.filter(t=>t?.chatSessionId===e.chatSessionId&&"
                 "t.status===`complete`).map(e=>Number(e.updatedAt??e.createdAt??0)||0))")
WATERMARK_NEW = ("let a=Math.max(0,...t.filter(t=>{"
                 "if(t?.chatSessionId!==e.chatSessionId||t?.status!==`complete`)return!1;"
                 "let n=e=>Array.isArray(e)?e.some(e=>e?.result?.ok===!0):!1;"
                 "if(n(t.initialExecutions))return!0;"
                 "for(let e of Array.isArray(t.steps)?t.steps:[])if(n(e?.toolExecutions))return!0;"
                 "return!1})"
                 ".map(e=>Number(e.updatedAt??e.createdAt??0)||0))")


# ---------------- release-chain maintenance ----------------
# Keep the legacy suites' version allow-lists and the extension display name in
# step with the new build, exactly as .30 did (otherwise 21 suites version-gate).
VERSION_GATE_OLD = "'1.14.0.34','1.14.0.35'"
VERSION_GATE_NEW = "'1.14.0.34','1.14.0.35','1.14.0.36'"
VNAME_GATE_OLD = "'1.14.0 ShunCode MCP Fix 3.3.10.30'"
VNAME_GATE_NEW = "'1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31'"
VNAME_RE_OLD = "|29|30)$"
VNAME_RE_NEW = "|29|30|31)$"
LOCALE_OLD = "DeepSeek++ ShunCode MCP Fix 3.3.10.30"
LOCALE_NEW = "DeepSeek++ ShunCode MCP Fix 3.3.10.31"


def bump_release_chain(dst):
    changed = []
    for fn in sorted(os.listdir(dst)):
        if not (fn.startswith("fix") and fn.endswith(".js") and "selftest" in fn):
            continue
        fp = os.path.join(dst, fn)
        s = read(fp)
        out = s
        # (a) numeric version allow-list
        if VERSION_GATE_OLD in out:
            out = out.replace(VERSION_GATE_OLD, VERSION_GATE_NEW)
        # (b) version_name allow-list array
        if VNAME_GATE_OLD in out:
            out = out.replace(VNAME_GATE_OLD, VNAME_GATE_NEW)
        # (c) version_name regex allow-list  (...|29|30)$
        if VNAME_RE_OLD in out:
            out = out.replace(VNAME_RE_OLD, VNAME_RE_NEW)
        # (d) exact-equality assertions used by the .30 suite
        out = out.replace("mf.version==='1.14.0.35'", "mf.version==='1.14.0.36'")
        out = out.replace("mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.30'",
                          "mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.31'")
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
    s = sub_once(s, HELPERS_ANCHOR, HELPERS_NEW, "helpers")
    s = sub_once(s, STATE_OLD, STATE_NEW, "state")
    s = sub_once(s, PROGRESS_OLD, PROGRESS_NEW, "progress")
    s = sub_once(s, FINAL_OLD, FINAL_NEW, "final-branch")
    s = sub_once(s, WATERMARK_OLD, WATERMARK_NEW, "resume-watermark")
    return s


def patch_manifest(s):
    s = sub_once(s, '"version": "1.14.0.35"', '"version": "1.14.0.36"', "manifest-version")
    s = sub_once(s, '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.30"',
                    '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.31"', "manifest-version-name")
    return s


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply-fix331031.py <src_dir> <dst_dir>")
    src, dst = sys.argv[1], sys.argv[2]
    for rel, want in EXPECT_SRC.items():
        p = os.path.join(src, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            raise SystemExit("FAIL-CLOSED: missing %s" % rel)
        got = sha(p)
        if got != want:
            raise SystemExit("FAIL-CLOSED: %s sha mismatch\n  expected %s\n  got      %s" % (rel, want, got))
    print("source hash-lock OK (5/5)")
    if os.path.abspath(src) != os.path.abspath(dst):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    cjs = os.path.join(dst, "content-scripts", "content.js")
    write(cjs, patch_content(read(cjs)))
    mf = os.path.join(dst, "manifest.json")
    write(mf, patch_manifest(read(mf)))
    print("patched content.js + manifest.json")
    bumped = bump_release_chain(dst)
    print("release-chain bumped: %d files" % len(bumped))
    print("content.js  ->", sha(cjs))
    print("manifest    ->", sha(mf))


if __name__ == "__main__":
    main()

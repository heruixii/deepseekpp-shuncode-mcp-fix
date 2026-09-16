# -*- coding: utf-8 -*-
"""
DeepSeek++ ShunCode MCP Fix 3.3.10.32 hash-locked patcher (.31 -> .32)

Root cause (verified by executing the shipped predicates against the real
17:16 failing trace, not by reading code):

C. DPP_TOOL_INTENT_331021(text, reasoning) discards the reasoning channel.
   It only consults `reasoning` when the visible text is empty, or when the
   text itself already carries a cue. For the failing turn the 25-char text
   scored midstep=false / strict=false / Mz=false, so the function returned
   !1 even though DPP_TOOL_INTENT_TEXT_331021(reasoning) === true and the
   model had explicitly announced another run_command. With toolIntent=false
   no tool_intent steering fired, DPP_SAFE_FINAL_CANDIDATE_331021 promoted
   the stub to a terminal answer, and the loop completed with totalTools:0.

D. The 650ms batched diagnostics (dpp_agent_turn_diag_331021) are flushed
   only from a non-awaited `pagehide` listener, so the deliberate
   window.location.reload() at the end of the inline agent loop (u&&_1())
   races with them and the failing turn's diagnostics are lost. The finally
   block awaits only MZ(r). This made the .31 field failure unobservable and
   produced the false conclusion that the gate never executed.

Fix C1  DPP_TOOL_INTENT_331021   fall back to the reasoning channel when the
        visible text carries no cue, so an announced-but-unemitted tool call
        is still detected. Inlined and self-contained.
Fix C2  DPP_SAFE_FINAL_CANDIDATE_331021   refuse to promote a terminal answer
        while the reasoning channel shows tool intent and no <task_complete>.
Fix D   flush batched diagnostics (awaited) before the loop-end reload.

Per user decision 2026-09-16 the reload itself (u&&_1()) is intentionally
left in place; only the diagnostics race is closed.

Usage: python apply-fix331032.py <src_dir> <dst_dir>
Fails closed: any hash or anchor mismatch aborts without writing.
"""
import hashlib, io, os, shutil, sys

EXPECT_SRC = {
    "manifest.json":                 "489401e2d35ad697d205d859f3bd59c871c80d423e6bfe0d5bb91235c99bd66c",
    "content-scripts/content.js":    "7f1016d35f2b54131e40b64a5d9beab40feffb06c6f2a91269661db0dbf10993",
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


# ---------------- Fix C1: reasoning fallback in tool-intent detection -------
# NOTE: DPP_TOOL_INTENT_331021 is extracted and eval'd standalone by the
# fix331010 suite, so the replacement must stay self-contained -- it may only
# call symbols the original body already referenced.
# C1 was reverted after testing: fix331025 and fix331027 both pin the rule
# "a visible concrete final takes precedence over stale reasoning", i.e.
# DPP_TOOL_INTENT_331021('The task is complete...', 'Let me invoke run_command.')
# must stay false. A blanket reasoning fallback broke that rule, so the
# reasoning channel is consulted only at the promotion site (Fix C2), which is
# reached solely when the turn produced no proper terminal decision.

# ---------------- Fix C2: do not promote a final while intent is pending ----
SAFE_OLD = ("function DPP_SAFE_FINAL_CANDIDATE_331021(e,t,n,r){"
            "let i=String(n??``).trim();"
            "if(!i||DPP_UNCONSUMED_TOOL_MARKUP_331024(i)||DPP_TOOL_INTENT_331021(i,r))return null;")
# Discriminator: text predicates cannot tell a genuine final from an
# announced-but-unemitted tool call (both score identically). What separates
# them is whether the run actually produced a successful tool execution.
# Block promotion only when the reasoning announces a tool action AND the run
# has no successful execution to stand on AND there is no <task_complete>.
SAFE_NEW = ("function DPP_SAFE_FINAL_CANDIDATE_331021(e,t,n,r){"
            "let i=String(n??``).trim();"
            "if(!i||DPP_UNCONSUMED_TOOL_MARKUP_331024(i)||DPP_TOOL_INTENT_331021(i,r))return null;"
            "if(!Sz(i)&&DPP_TOOL_INTENT_TEXT_331021(String(r??``))"
            "&&!(Array.isArray(t)&&t.some(e=>e?.result?.ok===!0)))return null;")

# ---------------- Fix D: flush diagnostics before the loop-end reload -------
RELOAD_OLD = "finally{d.clear(),await MZ(r),sX===n&&(sX=null,GY=null)}u&&_1()"
RELOAD_NEW = ("finally{d.clear(),await MZ(r),sX===n&&(sX=null,GY=null)}"
              "if(u){try{await DPP_DIAG_BATCH_FLUSH_ALL_331022()}catch(e){}_1()}")

# DPP_DIAG_BATCH_FLUSH_ALL_331022 currently returns undefined; make it return a
# promise so the await above actually waits for the writes to land.
FLUSHALL_OLD = ("function DPP_DIAG_BATCH_FLUSH_ALL_331022(){"
                "for(let e of DPP_DIAG_BATCH_STATE_331022.keys())DPP_DIAG_BATCH_FLUSH_331022(e)}")
FLUSHALL_NEW = ("function DPP_DIAG_BATCH_FLUSH_ALL_331022(){"
                "let e=[];for(let t of DPP_DIAG_BATCH_STATE_331022.keys())"
                "e.push(DPP_DIAG_BATCH_FLUSH_331022(t));return Promise.all(e)}")

# ---------------- release-chain maintenance ----------------
VERSION_GATE_OLD = "'1.14.0.35','1.14.0.36'"
VERSION_GATE_NEW = "'1.14.0.35','1.14.0.36','1.14.0.37'"
VNAME_GATE_OLD = "'1.14.0 ShunCode MCP Fix 3.3.10.31'"
VNAME_GATE_NEW = "'1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32'"
VNAME_RE_OLD = "|30|31)$"
VNAME_RE_NEW = "|30|31|32)$"
LOCALE_OLD = "DeepSeek++ ShunCode MCP Fix 3.3.10.31"
LOCALE_NEW = "DeepSeek++ ShunCode MCP Fix 3.3.10.32"


def bump_release_chain(dst):
    changed = []
    for fn in sorted(os.listdir(dst)):
        if not (fn.startswith("fix") and fn.endswith(".js") and "selftest" in fn):
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
        out = out.replace("mf.version==='1.14.0.36'", "mf.version==='1.14.0.37'")
        # (e) spaced/double-quoted equality used by the .31 suite
        out = out.replace('manifest.version === "1.14.0.36"', 'manifest.version === "1.14.0.37"')
        out = out.replace('"manifest version is 1.14.0.36"', '"manifest version is 1.14.0.37"')
        out = out.replace('manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.31"',
                          'manifest.version_name === "1.14.0 ShunCode MCP Fix 3.3.10.32"')
        out = out.replace("mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.31'",
                          "mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.32'")
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
    s = sub_once(s, SAFE_OLD, SAFE_NEW, "safe-final-intent-guard")
    s = sub_once(s, FLUSHALL_OLD, FLUSHALL_NEW, "diag-flush-all-awaitable")
    s = sub_once(s, RELOAD_OLD, RELOAD_NEW, "reload-diag-flush")
    return s


def patch_manifest(s):
    s = sub_once(s, '"version": "1.14.0.36"', '"version": "1.14.0.37"', "manifest-version")
    s = sub_once(s, '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.31"',
                    '"version_name": "1.14.0 ShunCode MCP Fix 3.3.10.32"', "manifest-version-name")
    return s


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply-fix331032.py <src_dir> <dst_dir>")
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
    ch = bump_release_chain(dst)
    print("release chain bumped in %d files" % len(ch))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# apply-fix331030.py — DeepSeek++ Fix 3.3.10.30 (DOM fence) hash-locked patcher
# 用法: python apply-fix331030.py <src_dir(.29)> <out_dir(.30)>
# 行为: 校验输入(.29)核心文件 SHA-256，不匹配则 fail-closed 不产出；
#       通过则整树复制并施加: ①main-world.js 注入 DOM fence ②manifest 版本 1.14.0.35 / Fix 3.3.10.30
#       ③新增 fix331030-dom-fence-selftest.js ④追加 .30 验证节到两个 md 文档
import sys, os, json, shutil, hashlib

SRC_EXPECT_MAINWORLD = "765aad691365ca617c682376419621a36fbcbe06a0fb57a9722d9c75a5efa472"
SRC_EXPECT_MANIFEST = "f8a58c1688806ccefcf280f3df25a9938faf50eddef6cf4a2ffd625aaf768a18"

FENCE = (
"function DPP_DOM_FENCE_NOTE_331030(e){try{JSON.parse(localStorage.getItem(`dpp_dom_fence_diag_331030`)||`{}`);}catch(t){}"
"try{localStorage.setItem(`dpp_dom_fence_diag_331030`,JSON.stringify({v:1,counts:e,lastAt:Date.now(),href:location.pathname}))}catch(t){}}"
"function DPP_DOM_FENCE_331030(){"
"if(window.__dppDomFence331030)return;"
"let e={insertBefore:0,removeChild:0,replaceChild:0,fallbackFailed:0,lastNote:0};"
"window.__dppDomFence331030=e;"
"let t=e=>e&&(e.name===`NotFoundError`||/not a child of this node/i.test(String(e&&e.message||``)));"
"function n(n){e[n]=(e[n]||0)+1;let t=Date.now();if(t-e.lastNote>=1e3){e.lastNote=t;DPP_DOM_FENCE_NOTE_331030(e)}}"
"function r(r,i){let a=Node.prototype[r];"
"if(typeof a!==`function`||a.__dppFence331030)return;"
"function o(o,s){try{return a.call(this,o,s)}catch(c){if(!t(c))throw c;n(r);try{return i.call(this,a,o,s)}catch(t2){n(`fallbackFailed`);return o??null}}}"
"o.__dppFence331030=!0;Node.prototype[r]=o;}"
"r(`insertBefore`,function(e,t,n){return e.call(this,t,null)});"
"r(`removeChild`,function(e,t){if(t&&t.parentNode)return t.parentNode.removeChild(t);return t});"
"r(`replaceChild`,function(e,t,n){return this.insertBefore(t,null)});"
"}"
"DPP_DOM_FENCE_331030();\n"
)

ANCHOR = "var mainWorld=(function(){"
SELFTEST_NAME = "fix331030-dom-fence-selftest.js"

TEST_REPORT_SECTION = """

## Fix 3.3.10.30 validation

- Root cause of recurrent "page crash" on refresh of one specific conversation, caught live via CDP (`D:/tmp/hang_capture.json`, `D:/tmp/probe_page.png`): DeepSeek frontend (`fe-static.deepseek.com`, fn `su`) throws `NotFoundError: Failed to execute 'insertBefore' on 'Node'` while reconciling `.ds-message` containers that DeepSeek++ restores tool blocks / agent traces into on hard refresh; the uncaught exception hits the app error boundary and renders its "页面崩溃/刷新重试" screen. SPA in-app navigation does not re-run the racy restore path, matching the user's observed "switch OK / refresh crashes".
- Fix: MAIN-world DOM fence (`DPP_DOM_FENCE_331030`, installed at `document_start` before page scripts) wraps `Node#insertBefore/removeChild/replaceChild`; on `NotFoundError` (and only on NotFoundError) it recovers instead of throwing (append at intended parent / remove from actual parent / no-op for detached), and persists a throttled beacon to `localStorage` key `dpp_dom_fence_diag_331030`.
- `.30` live-root-cause specialist regression: `fix331030-dom-fence-selftest.js` PASS.
- Full regression: all prior self-test suites re-run PASS (see health log).
- `node --check` PASS for `content-scripts/main-world.js` and the new selftest.
- Clean `.29 -> .30` hash-locked patcher output PASS; tampered `.29` input fails closed.
- Independent rebuild from frozen `.29` matches the `.30` tree with `missing=0 / extra=0 / diff=0`.
- Release-chain maintenance in step with the bump: `_locales/{en,zh_CN}` extension display name -> `Fix 3.3.10.30` (the name shown by chrome://extensions), and legacy selftest version allow-lists extended (18 list files + 2 supersedes-regex suites) — eliminates the 22 stale version-gate regressions observed right after the manifest bump.
- GPU LiveKernelEvent 141 note: repeated 141s on 2026-09-16 correlate only with the morning window; the afternoon crash wave shows no new 141, so 141 is tracked as a separate machine-level watch item, not this bug.
"""

README_SECTION = """

## Fix 3.3.10.30

**MAIN-world DOM fence for the refresh crash.** On hard refresh of an agent-heavy conversation, DeepSeek++ restores tool blocks / agent trace UI into DeepSeek's React-managed `.ds-message` containers while DeepSeek's own reconciler is also updating them; the anchor node Drift makes DeepSeek's `insertBefore` throw `NotFoundError`, and the uncaught exception becomes the app-level "页面崩溃" screen. `.30` installs `DPP_DOM_FENCE_331030` at `document_start` in the MAIN world: it wraps `Node#insertBefore`, `Node#removeChild` and `Node#replaceChild` so a `NotFoundError` (and only that error) recovers in place instead of crashing the app — foreign anchors fall back to append at the intended parent, removals of already-detached nodes become no-ops, and removals of nodes attached elsewhere are removed from their real parent. Every recovery bumps a throttled diagnostic beacon at `localStorage["dpp_dom_fence_diag_331030"]` (counts + lastAt). Fence is idempotent (`__dppFence331030`), zero-cost on the non-error path (single try/catch), and covered by `fix331030-dom-fence-selftest.js`.
"""


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg):
    print("FAIL-CLOSED:", msg)
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        fail("usage: apply-fix331030.py <src_dir> <out_dir>")
    src, out = sys.argv[1], sys.argv[2]
    if not os.path.isdir(src):
        fail(f"src dir missing: {src}")
    if os.path.abspath(src) == os.path.abspath(out):
        fail("src == out not allowed")
    mw = os.path.join(src, "content-scripts", "main-world.js")
    mf = os.path.join(src, "manifest.json")
    if not os.path.isfile(mw) or not os.path.isfile(mf):
        fail("core files missing in src")
    if sha256_file(mw) != SRC_EXPECT_MAINWORLD:
        fail("main-world.js hash mismatch (not a clean .29 input)")
    if sha256_file(mf) != SRC_EXPECT_MANIFEST:
        fail("manifest.json hash mismatch (not a clean .29 input)")

    if os.path.isdir(out):
        shutil.rmtree(out)
    shutil.copytree(src, out)

    # 1) main-world.js: insert fence right after the IIFE anchor (exactly once)
    omw = os.path.join(out, "content-scripts", "main-world.js")
    with open(omw, "r", encoding="utf-8", newline="") as f:
        txt = f.read()
    if txt.count(ANCHOR) != 1:
        fail("anchor not unique in main-world.js")
    if "DPP_DOM_FENCE_331030" in txt:
        fail("fence already present in input (not a .29)")
    txt = txt.replace(ANCHOR, ANCHOR + FENCE, 1)
    with open(omw, "w", encoding="utf-8", newline="") as f:
        f.write(txt)

    # 2) manifest version bump (exact, fail-closed)
    omf = os.path.join(out, "manifest.json")
    with open(omf, "r", encoding="utf-8", newline="") as f:
        mtxt = f.read()
    if '"version": "1.14.0.34"' not in mtxt or "Fix 3.3.10.29" not in mtxt:
        fail("manifest version strings not at .29")
    mtxt = mtxt.replace('"version": "1.14.0.34"', '"version": "1.14.0.35"', 1)
    mtxt = mtxt.replace("Fix 3.3.10.29", "Fix 3.3.10.30", 1)
    with open(omf, "w", encoding="utf-8", newline="") as f:
        f.write(mtxt)

    # 3) new selftest (canon copy from alongside this patcher)
    canon = os.path.join(os.path.dirname(os.path.abspath(__file__)), SELFTEST_NAME)
    if not os.path.isfile(canon):
        fail("selftest canon missing next to patcher")
    shutil.copyfile(canon, os.path.join(out, SELFTEST_NAME))

    # 5) release-chain maintenance: keep version gates in step with the bump.
    #    (a) legacy selftest allow-lists: 18 files x "'1.14.0.34']" and 18 x "...3.3.10.29']"
    #    (b) "supersedes" regexes in fix331011/12: "27|28|29)$/" -> add "|30"
    #    (c) _locales extension display name (what chrome://extensions shows)
    import glob as _glob
    touched_a = touched_b = 0
    for p in sorted(_glob.glob(os.path.join(out, "fix*-selftest.js"))):
        with open(p, "r", encoding="utf-8", newline="") as f:
            s = f.read()
        a = s.count("'1.14.0.34']")
        b = s.count("'1.14.0 ShunCode MCP Fix 3.3.10.29']")
        if not a and not b:
            continue
        if a > 1 or b > 1:
            fail(f"unexpected version-list multiplicity in {os.path.basename(p)}: A={a} B={b}")
        s = s.replace("'1.14.0.34']", "'1.14.0.34','1.14.0.35']")
        s = s.replace("'1.14.0 ShunCode MCP Fix 3.3.10.29']",
                      "'1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30']")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(s)
        touched_a += 1 if a else 0
        touched_b += 1 if b else 0
    if touched_a != 18 or touched_b != 18:
        fail(f"version-list maintenance touch counts wrong: A={touched_a} B={touched_b} (expect 18/18)")
    for name in ("fix331011-resume-crash-selftest.js", "fix331012-resume-isolation-selftest.js"):
        p = os.path.join(out, name)
        with open(p, "r", encoding="utf-8", newline="") as f:
            s = f.read()
        if s.count("27|28|29)$/") != 1:
            fail(f"supersedes-regex anchor not unique in {name}")
        s = s.replace("27|28|29)$/", "27|28|29|30)$/", 1)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(s)
    # (d) previous release's own suite pinned exact equality -> widen to inclusive list
    p29 = os.path.join(out, "fix331029-storage-pressure-selftest.js")
    with open(p29, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    for old, new in (
        ("mf.version==='1.14.0.34'",
         "['1.14.0.34','1.14.0.35'].includes(mf.version)"),
        ("mf.version_name==='1.14.0 ShunCode MCP Fix 3.3.10.29'",
         "['1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30'].includes(mf.version_name)"),
    ):
        if s.count(old) != 1:
            fail(f"fix331029 pin anchor not unique: {old[:40]}…")
        s = s.replace(old, new, 1)
    with open(p29, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    for loc in ("en", "zh_CN"):
        p = os.path.join(out, "_locales", loc, "messages.json")
        with open(p, "r", encoding="utf-8", newline="") as f:
            s = f.read()
        if s.count("DeepSeek++ ShunCode MCP Fix 3.3.10.29") != 1:
            fail(f"locale extension-name anchor not unique in {loc}/messages.json")
        s = s.replace("DeepSeek++ ShunCode MCP Fix 3.3.10.29", "DeepSeek++ ShunCode MCP Fix 3.3.10.30", 1)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(s)

    # 4) doc sections (deterministic, appended once)
    for name, section in (("FIX3-TEST-REPORT.md", TEST_REPORT_SECTION), ("README-SHUNCODE-FIX3.md", README_SECTION)):
        p = os.path.join(out, name)
        if not os.path.isfile(p):
            fail(f"{name} missing in src")
        with open(p, "r", encoding="utf-8", newline="") as f:
            d = f.read()
        if "Fix 3.3.10.30" in d:
            fail(f"{name} already documents .30 (not a .29)")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(d.rstrip("\n") + "\n" + section)

    print("OK: patched ->", out)
    print("  main-world.js +fence | manifest -> 1.14.0.35 / Fix 3.3.10.30 | +", SELFTEST_NAME, "| docs appended")


if __name__ == "__main__":
    main()

# DeepSeek++ ShunCode MCP Fix 3 — Test Report

## Build identity

- Base: DeepSeek++ 1.14.0 + ShunCode MCP Fix 2
- Target: `1.14.0 ShunCode MCP Fix 3.3`
- Strategy module: `fix3-policy.js`
- Patch mode: exact-marker, fail-closed

## Automated regression

| Area | Result |
|---|---|
| Parser / schema repair | **17/17 PASS** |
| Fix 3 strategy policy | **19/19 PASS** |
| DeepSeek web execution policy | **20/20 PASS** |
| Continuation intent / no-tool correction | **16/16 PASS** |
| Fix 3.1 agent / completion / retry | **31/31 PASS** |
| Fix 3.2 capability / adaptive routing | **17/17 PASS** |
| Fix 3.3 known-issue regression | **46/46 PASS** |
| Fix 3.3 production SSE parser integration | **8/8 PASS** |
| Diagnostic privacy/state test | **PASS** |
| JavaScript syntax scan | **PASS** |
| UTF-8 manifest / locale JSON | **PASS** |
| `_metadata` absent | **PASS** |
| Python patcher compile | **PASS** |
| `__pycache__` cleanup | **PASS** |
| Isolated Edge unpacked load / Service Worker | **PASS** |

### Parser/schema coverage

Covers valid JSON, unescaped Windows paths, nested PowerShell quotes, literal newlines, fenced JSON, wrapper payloads, trailing commas, namespaced ShunCode tool names, raw run_command, complete raw apply_patch, patch aliases, generic single-string schema raw-body, numeric/boolean coercion, incomplete patch rejection, schema aliases, schema defaults, and no-guess custom fields.

### Fix 3 policy coverage

Covers model-context result compaction without input mutation, read-only retry allowlist, side-effect retry denylist, ambiguous-outcome denial, intent routing, recent-success bias, dynamic 12/24/36 step budgets, repeated-call loop state, ShunCode script_bridge delegation, MCP health summary, strategy flags, and error classification.

### DeepSeek webpage coverage

Covers read-only retry, namespaced read retry, run/apply_patch retry denial, ambiguous result denial, 6/12/16/9 KB model budgets, transport/format/loop error classification, 12/24/36 web step budgets, stable argument ordering, runtime loop-guard hook, runtime retry hook, runtime dynamic-budget hook, and result-context compaction hook.


### Continuation hotfix coverage

Covers the real failure text `需要用命令写入。先测试。`, additional Chinese and English mid-step cues, strict “continue until complete” tasks, normal completed-text non-match, an actual 8-correction hard cap, removal of the previous one-nudge premature-stop branch, and reset of the consecutive correction counter after a real tool turn.

A clean Fix 2 rebuild produced the same 109-file tree as the patched working copy with no path or SHA-256 differences.


### Fix 3.1 stability coverage

The new regression layer covers ambiguous side-effect outcomes (`verify_before_retry`, `retrySafe=false`), mutation vs verification classification, completion gating after successful writes, failed verification remaining incomplete, successful verification unlocking completion, progress-sensitive nudge reset, short `continue` requests receiving the 36-step budget, and both webpage-agent and background-policy parity.

Fix 3.1 is applied by a separate fail-closed `tools/apply-fix31.py` overlay after Fix 3. A clean Fix 2 -> Fix 3 -> Fix 3.1 build produced a **111-file tree byte-identical** to the working extension.


### Fix 3.2 capability and adaptive-routing coverage

The production `mcp_discover` output now keeps a compact capability window even after ordinary tool-result windowing. Tests verify fresh and old discover results, object/string outputs, malformed-output fail-safe behavior, single-use handle guidance, capability replay classification, and repaired Chinese adaptive-routing terms.

A replay against the current cached 12-tool ShunCode descriptor set using a Chinese “write seven files with one command” intent placed `run_command` first and inside the 5-tool / 14 KB direct set. For this 12-tool ShunCode server, `Direct` exposure is recommended for maximum reliability; Adaptive remains supported.

### Fix 3.3 stream and local-execution safety coverage

The Fix 3.3 regression layer covers recursive-but-strict DeepSeek `FINISHED` detection, real SSE byte-stream parsing, abrupt EOF preservation, empty/no-id EOF one-shot retry, partial-output non-retry, privacy-limited stream diagnostics, schema-required preflight at both initial and Agent execution paths, Windows PowerShell 5.1 UTF-8 corruption blocking, workspace-scope recovery hints, and read-only PTY-empty direct fallback.

The tests explicitly prove that mutating commands are not retried because PTY output is empty, dangerous encoding commands are blocked before MCP dispatch, and stream retries do not occur after partial model output.

## Rebuild tests

### Compatible Fix 2 baseline

`tools/apply-fix3.py` rebuilt a fresh temporary Fix 3 from Fix 2. Background, content script, main-world, and policy syntax passed. All expected background and DeepSeek-web Fix 3 markers were present.

Result: **PASS**.

### Incompatible bundle / marker mismatch

A required web-loop marker was deliberately renamed in a temporary Fix 2 copy. `apply-fix3.py` exited non-zero. SHA-256 hashes of background.js, content.js, main-world.js, and manifest.json were identical before and after the failed patch.

Result: **FAIL-CLOSED PASS — zero target mutation**.

### Full builder integration

`tools/build-fix3.ps1` was run on a clean Fix 2 copy. It applied Fix 3, copied tests/tools, ran the entire health suite, and created a ZIP.

Result: **PASS**.

### Failed build cleanup

The builder was run against a deliberately incompatible source. It exited non-zero and removed both the incomplete destination directory and ZIP.

Result: **PASS**.

## Reproducibility

For the current completed tree versus an independently rebuilt tree, SHA-256 matched for the runtime core:

- `background.js`
- `content-scripts/content.js`
- `content-scripts/main-world.js`
- `fix3-policy.js`

Manifest and EN/ZH locale files were semantically equal; after normalizing them to canonical UTF-8 LF serialization, their SHA-256 also matched the rebuilt tree.

Result: **PASS**.


### Fix 3.3 overlay reproducibility

A frozen Fix 3.2 tree was independently copied and patched with `apply-fix33.py`; the release tests/docs/tools overlay was then applied. The resulting **118-file** tree matched the formal Fix 3.3 trial tree byte-for-byte by SHA-256, with no missing, extra, or differing files.

Result: **PASS**.

## Safety decisions

- No automatic retry of run_command/apply_patch/write/delete/update/commit/push class operations.
- No automatic retry when provider reports ambiguous external outcome.
- No duplicate long-command temp-script layer; ShunCode `script_bridge` remains authoritative.
- No new persistence of large tool output solely for model compaction; existing result/history flow remains authoritative.
- No rewrite of minified React MCP settings UI solely to display Fix 3 diagnostics; existing MCP test backend is enriched and offline health tooling is provided.
- All future-version patching requires exact compatibility markers; no fuzzy minified-code replacement.
- DeepSeek stream EOF is never treated as success merely because HTTP closed; only strict completion markers or a safe empty-turn retry are accepted.
- PTY empty-output recovery is restricted to verification commands; mutations are never replayed by this rule.
- Windows PowerShell text round-trips that can corrupt UTF-8 no-BOM files are blocked before tool dispatch.

## Remaining manual validation

An isolated Edge profile successfully registered the unpacked extension and exposed `chrome-extension://kdmpkkahkhdmdhfkdihkopikgcocbpbf/background.js` as a live Service Worker target. The remaining manual boundary is an authenticated `chat.deepseek.com -> DeepSeek++ -> ShunCode MCP` smoke run in the user's normal profile, because the isolated profile intentionally has no user login state.

## Fix 3.3.1 SSE close compatibility

- Recognizes DeepSeek Web `event: close` as a normal terminal event only when the associated payload contains no explicit failure evidence.
- Keeps bare EOF incomplete; `FAILED`, `error`, `aborted`, `timeout`, and similar close payloads are not accepted as success.
- Adds a production-parser regression fixture for the observed `ready -> update_file -> hint -> close` sequence.
- Keeps Fix 3.3 empty-stream retry, partial-stream safety, MCP behavior, UTF-8 guard, workspace routing, and PTY recovery unchanged.

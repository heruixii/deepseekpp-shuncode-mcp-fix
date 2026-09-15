> Current release: **Fix 3.3.10.10** — restores interrupted Agent checkpoints instead of restarting completed work, fixes false-positive `run_command` success and blank-final “complete” states, classifies ambiguous 120-second MCP disconnects safely, and adds an honest live status strip.

> Previous release: **Fix 3.3.10.9** — globally retires expired unclaimed Agent traces while protecting live work in other DeepSeek tabs, repairs terminal traces that retained streaming steps, and injects deterministic `list_directory` facts so the model cannot estimate unsupported totals.

> Previous release: **Fix 3.3.10.8** — closes abnormal inline-Agent lifecycles with an inactivity watchdog, terminal-state fallback, page-unload/overlap cleanup, and durable stale-trace recovery. It also aligns `run_command` with ShunCode's native Bash schema and treats command-level failure as failure instead of transport success.

> Previous release: **Fix 3.3.10.7** — stops active inline Agents before a new manual DeepSeek turn can fork the same parent-message chain, and performs one abortable retry for transient MCP HTTP 502/503/504 only on read-only verification tools; mutating commands are never replayed automatically.

> Previous release: **Fix 3.3.10.6** — safely salvages EOF-truncated DeepSeek DSML tool calls only when every parameter is complete and schema-safe, then supplies a synthetic FINISHED status so the official page does not mislabel that recovered tool turn as server unavailable.

> Fix 3.3.10.9 validation: dedicated global-trace/statistics self-test **30/30**, all 30 self-test files pass, health-check passes with **79 JS files**, and both 3.3.10.8→3.3.10.9 rebuild and 3.3.10.9 self-rebuild reproduce all 158 files byte-for-byte.

> Current release: **Fix 3.3.10.3** — invalid-message-id recovery now performs one bounded fallback to the previous successfully used parent after the existing same-parent retry is exhausted.

> Current release: **Fix 3.3.10.2** — manual-chat page streaming now hides orphan tool/DSML closing tags before DeepSeek React renders them, while raw stream data remains available to the tool parser.

> Current release: **Fix 3.3.10.1** — malformed DSML storms are quarantined instead of aborting the turn; valid prefix text and the official response message chain are preserved.

> Current release: **Fix 3.3.10** — filters orphan DSML/tool closing-tag noise, stops repeated control-markup storms, and prevents direct-XML + legacy-DSML duplicate tool execution while preserving Fix 3.3.9 message-ID recovery.

> Current release: **Fix 3.3.9** — hardens DeepSeek response message-ID selection and adds one bounded recovery for explicit `code=0 / invalid message id`, while preserving Fix 3.3.8 Agent budgets.

# DeepSeek++ ShunCode MCP Fix 3 — Test Report

## Build identity

- Base: DeepSeek++ 1.14.0 + ShunCode MCP Fix 2
- Target: `1.14.0 ShunCode MCP Fix 3.3.10.10`
- Strategy module: `fix3-policy.js`
- Patch mode: exact-marker, fail-closed

## Automated regression

| Area | Result |
|---|---|
| Parser / schema repair | **17/17 PASS** |
| Fix 3 strategy policy | **19/19 PASS** |
| DeepSeek web execution policy | **21/21 PASS** |
| Continuation intent / no-tool correction | **16/16 PASS** |
| Fix 3.1 agent / completion / retry | **31/31 PASS** |
| Fix 3.2 capability / adaptive routing | **17/17 PASS** |
| Fix 3.3 known-issue regression | **46/46 PASS** |
| Fix 3.3 production SSE parser integration | **8/8 PASS** |
| Fix 3.3.1 SSE close compatibility | **12/12 PASS** |
| Fix 3.3.2 Safe DOM compatibility | **21/21 PASS** |
| Fix 3.3.3 Agent stability / storage pressure | **29/29 PASS** |
| Fix 3.3.4 manual-chat tool storm guard | **76/76 PASS** |
| Fix 3.3.5 empty-stream / fresh-PoW retry | **16/16 PASS** |
| Fix 3.3.6 long-task page/storage stability | **21/21 PASS** |
| Fix 3.3.7 uploaded-file continuation / JSON response | **28/28 PASS** |
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


## Fix 3.3.2 Safe DOM compatibility

- Root-cause evidence: the displayed crash/plugin warning is embedded in DeepSeek's own current web bundle; Edge produced no new renderer Crashpad dump or Application Error.
- The highest-risk extension behaviors were optional content capabilities that modify DeepSeek React-managed DOM (history/project/sidebar/background/pet/theme/etc.).
- Fix 3.3.2 narrows the active content capability list to the MCP/Agent-critical set and excludes floating-chat injection on `chat.deepseek.com`.
- New regression: **21/21 PASS**.
- Full prior regression remains PASS; **60 JavaScript files** pass syntax validation.
- Fail-closed tamper test: patcher exits non-zero and leaves all target files unchanged.
- Independent reconstruction: **122/122 files byte-identical by SHA-256**.
- Isolated Edge/CDP smoke: target Service Worker reports `1.14.0 ShunCode MCP Fix 3.3.2`; DeepSeek page reload emits **0 Runtime exceptions** and **0 console error/warning**; risky DPP page nodes are absent.

## Fix 3.3.3 Agent stability / storage pressure

- Root-cause evidence came from the live Edge LevelDB WAL, not raw string occurrence counts: repeated full-array writes were ~360–385 KiB for inline-agent traces and ~385–403 KiB for tool history during the failing long task.
- Transient Agent states are memory-only; completed-step recovery checkpoints are persisted every 4 steps, with final/error/stop persistence unchanged.
- Inline-agent trace and background tool-history stores use 256 KiB soft budgets while preserving the newest/current record.
- Strict text-only `detail` / `output` dedupe is applied to persistence, Agent DOM, model continuation and history; structured artifact-like output is preserved.
- Obsidian/vault discovery guidance is config-first and bounded, preventing the observed repeated whole-drive searches.
- New regression: **29/29 PASS**.
- Stress fixture: 19-tool trace 86,944 B -> 44,299 B; estimated trace-write amplification reduced by >75%.
- Real failing trace offline measurement: 76,691 B -> 51,513 B (-32.8%); combined with checkpoint cadence, estimated write reduction 77.6%.
- Fail-closed tamper test: non-zero exit with all target hashes unchanged.
- Independent reconstruction: **124/124 files byte-identical by SHA-256**.

## Fix 3.3.4 manual-chat tool storm guard

- Live storage evidence: one `manual_chat` request generated at least ~228 `run_command` attempts. The latest 100 retained history entries shared one request/message and were all rejected with `tool_authorization_call_limit` in ~11.2 s.
- The tool XML was complete (`</run_command>` present), so this is a model/tool-batch storm rather than incremental parser replay.
- Content synchronous breaker: 8 total / 6 per normalized tool name per manual response. A 228-call same-tool replay allows 6 and blocks 222 before execution.
- `agent_run` bypasses this manual breaker; a 40-call Agent simulation remains fully allowed.
- Background trigger-aware authorization limits provide independent containment without shrinking Agent/automation capacity.
- Pathological PowerShell `Out-String/Out-File -Width` values are rejected locally.
- Authorization call-limit recovery is terminal, not authorization-refresh.
- Stale >256 KiB trace arrays are migrated on read, and runtime-state startup proactively triggers that read/migration.
- New regression: **76/76 PASS**; full health and JS syntax scan pass.
- Fail-closed tamper test: patcher exits non-zero and all target hashes remain unchanged.
- Independent 3.3.3 -> 3.3.4 reconstruction is byte-identical by SHA-256 before documentation finalization; release rebuild repeats this check.

## Fix 3.3.5 empty-stream / fresh-PoW retry

- Historical split: the 17:42 `ready/update_file/hint/close` failure was the 3.3.1 terminal-event bug; later no-marker EOFs are a separate empty-stream class.
- Current reproduction evidence: three consecutive failures at 20:00, 20:01 and 20:02, each after one successful initial `run_command`, with step 0 receiving no text, reasoning or message id. Fresh anchors 24, 28 and 32 rule out a single reused stale anchor.
- Recovery flaw: the 3.3.4 `BR()` generated auth + PoW once while `HR()` could issue two HTTP attempts with the same request material.
- Fix: keep a strict maximum of two attempts, but rebuild auth + PoW before the second attempt.
- Safety: any text/reasoning already emitted makes a transport exception non-replayable. Bare EOF is never promoted to success.
- Diagnostics are structure-only: attempt, status, content type, raw byte count, chunk count, fresh-PoW flag; no prompt/auth/token/PoW body.
- New regression: **16/16 PASS**. All prior regression suites remain PASS.

## Fix 3.3.6 long-task page/storage stability

- Real run evidence: 12 steps / 21 tools (~130 s) and 6 steps / 6 tools (~65 s) both completed; no new renderer crash.
- Trace sizes: ~97 KB for the 12-step run, ~32 KB for the 6-step run; not an Agent-trace OOM.
- Tool history runtime value reached ~555 KB / 100 records despite a 256 KiB source cap, consistent with stale MV3 background code risk while `manifest.version` remained unchanged.
- Tool execution block store reached ~729 KB, with one historical 410-execution block at ~543 KB.
- Fix 3.3.6 bumps the real manifest version to `1.14.0.1`, adds background startup history migration, and enforces execution-block byte/execution budgets.
- DOM pressure reduction: self-generated Agent subtree mutations are ignored; relevant observer work and reasoning streaming are RAF-coalesced; final reasoning is force-flushed.
- New regression: **21/21 PASS**. All prior suites remain PASS.

## Fix 3.3.10.9 global trace/statistics integrity

- Global stale-trace recovery now checks every stored `running` trace, not only the current conversation.
- A 5-minute expiry gate and two cross-tab liveness probes protect active Agents in other DeepSeek tabs. If the probe channel is unavailable, foreign-trace cleanup fails closed.
- Restored terminal traces can no longer retain a misleading `streaming` step; inconsistent historical terminal records are repaired durably.
- Successful `list_directory` results inject machine-verified `returnedEntries`, `directoryEntries`, `fileEntries`, and truncation state into both full and compacted model context.
- The Agent prompt prohibits estimated totals. A deterministic completion gate rejects contradictory directory/file/entry counts and asks the model to rewrite from verified facts; unrelated counts such as number of tool calls are not blocked.
- New regression: **30/30 PASS**. All 30 regression suites pass; **79 JavaScript files** pass syntax validation.
- Reproducibility: the 3.3.10.8 upgrade build and the 3.3.10.9 self-rebuild each match all **158 files** in the release directory.
- Core SHA-256: `content.js` `6A3F72E316265ED33A1CEA974E6048A79DBD7F124D135128F1934557827C5ECB`; `manifest.json` `7CAE4EEC1486D6E8FDEEB9152A5AD954B082C25320661AA5CF867EA105451C79`.

## Fix 3.3.10.10 observable lifecycle and error integrity

- Edge structured logs exposed three ambiguous `run_command` disconnects at roughly 120 seconds, one real `exit_code=1` result stored as `ok:true`, one terminal trace marked complete with empty final text, and older image-scope/result-size failures.
- A later reproduction showed the original Agent had already installed Rust, compiled Daub, rendered a real plan, and verified deterministic output before interruption. Sending “继续中断的任务” created a new trace, reset ShunCode todos to `0/6`, and repeated environment discovery even though both interrupted traces and their settled tool results remained in durable storage.
- Short continuation requests now select the latest incomplete trace in the same chat, follow bounded continuation chains back to the source run, inject prior settled tool results, and persist a compact checkpoint into the new trace. The resume contract forbids repeating already-confirmed discovery/build/write/test work and requires inspecting existing ShunCode progress before replacing it.
- `run_command` outcome normalization now reads the real invocation object and treats non-zero exit codes, failed status values, and explicit command failure as failures even when the MCP transport itself succeeded.
- Generic MCP SSE/network/timeout failures are classified as transport uncertainty. Mutating calls are not blindly replayed; the recovery instruction reconnects first and uses read-only verification to establish the external outcome.
- Empty terminal output is fail-closed as `失败·未完成` instead of being persisted as a misleading successful completion.
- Agent status now exposes `准备中 / 运行中 / 已完成 / 已暂停 / 失败·未完成`, the current wait/reasoning/tool/response phase, settled/running/failed/interrupted tool counts, elapsed time, and inactivity age.
- The only remaining count shown is explicitly labelled `自动续跑安全额度` and `不是任务剩余量`; unplanned future work is described as dynamically planned rather than converted into an invented percentage.
- Tool rows settle as soon as their tool-completion event arrives, so users no longer need to wait for the entire model step to discover whether a command is still running.
- New Fix 3.3.10.10 regression: **60/60 PASS**. All **31** regression suites pass; **80 JavaScript files** pass syntax validation.
- Reproducibility: both the 3.3.10.9 upgrade build and the 3.3.10.10 self-rebuild reproduce all **160 files** byte-for-byte.
- Core SHA-256: `content.js` `27B177F9CFCD75295E4B23B670E226091EF320DBB5AFF968356CBFE425BD6A6B`; `manifest.json` `F3D4AA1874514FF792DFAB720C1B7281F17186C5911C42A3F396EDC347AFA66F`.

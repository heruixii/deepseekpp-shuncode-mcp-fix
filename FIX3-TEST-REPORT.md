> Current release: **Fix 3.3.10.29** — live Fix 3.3.10.28 evidence showed the first task starting correctly, but the second task's page crashed around completion/persistence. The Agent loop itself finished cleanly (5 steps / 5 real tool actions, HTTP 200, no generation_err or Agent exception), while the extension wrote about 975 KB of Local Storage state in the short repro: ~536 KB usage history, ~252 KB Agent traces, ~131 KB tool history, ~55 KB turn diagnostics. The 15-second delayed usage flush aligned almost exactly with the large write. `.29` removes the 536 KB legacy usage array from the hot write path by writing new usage records into per-day v2 shards plus a small meta record; legacy v1 stays read-only for compatibility and is merged only on stats/history reads. Agent trace and tool-history disk budgets are also tightened from ~128 KB to ~64 KB. This reduces extension-side persistence pressure, but does **not** claim that the ambiguous Windows LiveKernelEvent 141 (which still referenced an old Aug-21 WATCHDOG dump) proves or is fixed as a GPU crash.

> Current release: **Fix 3.3.10.28** — no new `.27` Agent reproduction was present yet (DeepSeek IndexedDB advanced via page/cache activity while extension storage stayed at 12:59), so this release is a proactive hardening based on the already captured live failure chain. The old logs repeatedly showed `run_command` returning `status=completed`, `exit_code=0`, `total_output_bytes=0`, after which the model replayed a consumed single-use capability. `.28` makes capability readiness consumption-aware (any later `mcp_invoke` invalidates earlier discover/describe readiness until a fresh discover/describe occurs) and annotates successful empty-PTY command results as completed/consumed with a strict no-replay + fresh read-only verification instruction. It does not auto-retry neutral or mutating commands.

> Current release: **Fix 3.3.10.27** — live `.26` logs proved the remaining user-visible failure was not the previous generation_err loop: one Agent loop still hit `tool_intent_limit` after a successful capability discovery, and a later 12-step/11-tool loop was falsely marked complete on the exact text `页面内容已成功加载。继续读取剩余内容。` while its reasoning explicitly said only the first 25 of 421 lines had been read. Fix 3.3.10.27 adds a narrow direct-continuation classifier, lets manual escalation consult reasoning only when visible text is itself a continuation/mid-step (concrete final text still suppresses stale reasoning), and makes tool-intent steering capability-aware when recent successful mcp_discover/mcp_describe results already provide a real handle/schema. It still never synthesizes a handle, arguments, or tool call from reasoning.

> Current release: **Fix 3.3.10.26** — live logs showed five consecutive DeepSeek HTTP 200 SSE responses ending `INCOMPLETE + finish_reason=generation_err`. The previous recovery alternated full augmentation (~16.7 KB) and compact augmentation (~10.9 KB); after compact failure its “bypass” actually returned to full augmentation, creating a full/compact failure loop. Fix 3.3.10.26 adds a third, fail-safe `passthrough` stage: normal generation_err -> one compact retry -> raw original request with no DeepSeek++ prompt injection. If raw also fails, passthrough stays armed for the matching parent for 60 seconds instead of returning to full/compact. A separate 120-second generation-error streak map fixes the old failure counter resetting to 1 whenever one-shot recovery state was consumed. FINISHED clears both maps. No automatic network replay, tool synthesis, capability guessing, or authorization bypass is introduced.

> Current release: **Fix 3.3.10.25** — fixes two live state-machine gaps proven by the 2026-09-15 reproduction. First, completed manual DeepSeek turns could announce a real tool action only inside reasoning (`Let me invoke run_command`, `I need a fresh capability`) while visible text stayed empty; Fix 3.3.10.22 inspected visible text only, so Agent mode often did not start until the user's third attempt. This release carries only a bounded 4096-character reasoning tail across the ephemeral MAIN/content bridge and uses it solely as a boolean tool-intent classifier. Raw reasoning is not added to the Agent prompt, trace, or diagnostic storage. Second, generic no-tool continuation still used a one-shot boolean gate: after one nudge, another incomplete reasoning-only turn could require continuation while steering returned `none`, ending as `EMPTY_FINAL`. Fix 3.3.10.25 replaces that gate with an independent bounded counter (maximum 3 per step), resets it on a real tool call, and emits an explicit `generic_continuation_limit_331025` if exhausted. Tool-intent and generic budgets remain separate; FINISHED/manual/no-tool/no-resume safety gates remain authoritative, and no tool arguments or capabilities are inferred from reasoning.

> Current release: **Fix 3.3.10.24** — fixes a live parser/finalization failure where DeepSeek emitted `<tool_invoke>{"capability":...,"arguments":...}</tool_invoke>` after a successful `mcp_discover`. Fix 3.3.10.23 had already repaired the prior `h is not a function` Agent crash, and the same live session proved the Agent could execute 10+ real `run_command` steps. The fourth task then stopped because `<tool_invoke>` was not a registered tool tag: the parser treated it as ordinary text and the completion gate promoted the raw control markup to `finalText`. This release adds a strict compatibility bridge: only an exact `<tool_invoke>` JSON object with exactly `capability` + plain-object `arguments`, a valid `mcp_cap_...` handle, and an available `mcp_invoke` descriptor is normalized to **mcp_invoke**. It never dispatches `run_command` directly; the existing owner/session/TTL/single-use/schema checks remain authoritative. Malformed or ambiguous wrappers are not executed, `<tool_call>` is never auto-normalized, both generic wrappers are suppressed from visible stream text, and residual control markup is forbidden from final-answer promotion. It also fixes the live false-final sentence `我试试分享链接背后的数据接口。` / `Let me try ...` by expanding the mid-step gate. Because `mcp_discover` candidate summaries do not expose argument schemas, the Agent guidance now requires `mcp_describe` before `mcp_invoke` when arguments are not already verified instead of guessing optional fields (the earlier live `run_command.execution` INVALID_ARGUMENT is therefore addressed without unsafe parameter deletion).

> Validation: dedicated Fix 3.3.10.24 suite **43/43 PASS**; all **45 self-test suites PASS**; health checks **94 JavaScript files** plus all patchers. Manifest: `1.14.0.29 / 1.14.0 ShunCode MCP Fix 3.3.10.24`.

> Previous release: **Fix 3.3.10.23** — fixed deterministic Agent lexical-shadow crash (`h is not a function`) and reduced large-object storage pressure.

> Historical release: **Fix 3.3.10.23** — fixes a deterministic Agent crash proven by the latest live session. In `Jz.shouldStopAfterTurn`, the outer parent-message accessor `h=()=>...parentMessageId` was shadowed by an inner `let h=DPP_STAT_CLAIM_MISMATCH_33109(...)` added in 3.3.10.21. Once a discovered capability returned and the completion path reached turn-decision diagnostics, `responseMessageId:h()` called the shadowing value instead of the accessor and threw `h is not a function`. The local statistic binding is now uniquely named (`DPPStatMismatch331023`), health explicitly rejects the old shadow declaration, and Agent exceptions now persist bounded error/stack metadata for future diagnosis. The same live log also showed 4.65 MB of extension LevelDB writes dominated by whole-array usage/trace/execution/history rewrites, so this release halves trace/execution/tool-history byte budgets and delays usage flushes to 15 seconds while preserving the existing 180-day/5000-record usage retention contract.

> Validation: dedicated Fix 3.3.10.23 suite **31/31 PASS**; all **44 self-test suites PASS**; health checks **93 JavaScript files** and all patchers. Manifest: `1.14.0.28 / 1.14.0 ShunCode MCP Fix 3.3.10.23`.

> Previous release: **Fix 3.3.10.22** — manual tool-intent escalation, compact recovery circuit breaker, and diagnostic/usage batching.

> Historical release: **Fix 3.3.10.22** — addresses three failure layers proven by the 2026-09-15 live session `adb18f7b-418d-403b-8034-ad271f6a6c6f`: a finished manual completion can explicitly narrate `mcp_discover` / `run_command` / curl without emitting any executable tool call; compact `generation_err` recovery can itself fail and should not immediately recurse into compact mode; and extension diagnostics/usage telemetry were repeatedly rewriting large whole arrays during rapid retries. A FINISHED zero-tool manual response with explicit tool intent can now escalate into the existing authorized Agent path without synthesizing arguments or calls. A compact `generation_err` enters a single-use normal-mode cooldown for the exact next parent. Diagnostic rings are buffered/coalesced, and usage turns are burst-buffered with an in-memory cache while preserving the existing 180-day / 5000-record retention contract. No native Edge crash was proven by the incident, so this release treats page/renderer instability as a stability target rather than claiming to fix an `msedge.exe` process crash.

> Validation: dedicated Fix 3.3.10.22 behavior suite **42/42 PASS**; all **44 self-test suites PASS**; health checks **92 JavaScript files** plus every patcher. Manifest: `1.14.0.27 / 1.14.0 ShunCode MCP Fix 3.3.10.22`.

> Previous release: **Fix 3.3.10.21** — bounded Agent tool-intent steering and strict terminal promotion.

> Historical release: **Fix 3.3.10.21** — fixes the Agent no-tool dead end exposed after 3.3.10.20 successfully recovered `generation_err`. Real traces showed DeepSeek could repeatedly narrate an intended `run_command`/`mcp_invoke` action without emitting an executable tool call; the old generic nudge gate effectively allowed only one correction in the same no-tool step. 3.3.10.21 adds a separate, bounded tool-intent steering path (maximum 3 attempts per step), never guesses arguments or capability handles, resets immediately after a real tool execution, and fails closed when the conversation chain is not continuable. A strict terminal promotion can recover concrete final text but rejects narrated next-step/tool plans. New privacy-safe Agent-turn diagnostics persist only IDs, counters, lengths, booleans and terminal metadata — not prompt, reasoning, answer text or tool argument values.

> Validation: dedicated Fix 3.3.10.21 behavior suite **43/43 PASS**; all **43 self-test suites PASS**; health currently checks **91 JavaScript files** plus every patcher. Manifest: `1.14.0.26 / 1.14.0 ShunCode MCP Fix 3.3.10.21`.

> Previous release: **Fix 3.3.10.20** — parent-chain compact recovery for explicit DeepSeek `finish_reason=generation_err`.

> Historical release: **Fix 3.3.10.20** — adds a narrowly-scoped recovery path for DeepSeek HTTP 200/SSE responses that explicitly end with `finish_reason=generation_err`. The plugin does not replay the failed request itself. It arms a 12-second, single-use recovery only for the next request in the same chat whose `parent_message_id` exactly matches the failed assistant message, and uses a compact model-facing augmentation while preserving the full authorization descriptors for execution. The compact retry disables memory/project/preset/automatic-skill context for that one retry, keeps the system prompt, and strips verbose tool-schema prose. Parent/recovery metadata is recorded without prompt content so the next reproduction can prove whether the fallback was used.

> Previous release: **Fix 3.3.10.19** — capability alias recovery, durable zero-tool resume, and compact Agent UI.

> Current release: **Fix 3.3.10.19** — fixes capability protocol drift after `mcp_discover` without weakening MCP authorization: a unique, unexpired discovered candidate may be parsed through a temporary Agent-only alias, but execution still delegates to the original single-use `mcp_invoke` lease. It also makes explicit `继续/resume` able to start from an interrupted checkpoint even when the manual DeepSeek reply produced zero fresh tool calls, persists the first/mutation step more aggressively, and replaces the default Agent transcript with a compact Codex-style status surface that hides reasoning/control noise and exposes tool detail only on demand.

> Previous release: **Fix 3.3.10.18** — closes the pre-transport observability gap around manual sends such as “继续”: privacy-safe breadcrumbs record request stages from the send hook through augmentation and transport.

> Current release: **Fix 3.3.10.12** — isolates interrupted-task recovery from the DeepSeek page request/render path: the user prompt and trace stay unchanged, only the internal Agent receives a DSML-sanitized checkpoint, and historical tool objects are never replayed.

> Previous release: **Fix 3.3.10.11** — introduced a bounded resume checkpoint, but still rewrote the manual DeepSeek request and replayed historical tool objects; real-page testing showed that path could still destabilize the page.

> Previous release: **Fix 3.3.10.10** — restores interrupted Agent checkpoints instead of restarting completed work, fixes false-positive `run_command` success and blank-final “complete” states, classifies ambiguous 120-second MCP disconnects safely, and adds an honest live status strip.

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
- Target: `1.14.0 ShunCode MCP Fix 3.3.10.12`
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
- Fix 3.3.10.10 core SHA-256: `content.js` `27B177F9CFCD75295E4B23B670E226091EF320DBB5AFF968356CBFE425BD6A6B`; `manifest.json` `F3D4AA1874514FF792DFAB720C1B7281F17186C5911C42A3F396EDC347AFA66F`.

## Fix 3.3.10.11 safe resume gateway

- Edge storage showed the last normal Agent trace ending at 13:29, while the following “continue task” request produced no new trace. No new native Edge crash dump or Windows application crash event was created, placing the failure before Agent trace creation in the web request/render path.
- Manual resume augmentation is now fail-open: corrupt or unexpected history can no longer abort the normal DeepSeek request.
- The synchronous request checkpoint is plain text, strips raw DSML/tool-control markup, and is capped at 2,400 characters.
- Reused Agent tool history is deduplicated and capped at 12 calls, 24 KiB total, and 8 KiB per entry. Circular or unserializable records are skipped.
- Dedicated crash regression: **18/18 PASS**, including oversized histories, repeated executions, raw DSML, corrupt runtime state, and circular tool results.
- All **32** self-test suites pass; **81 JavaScript files** pass syntax validation. The clean 3.3.10.10 upgrade build and 3.3.10.11 self-rebuild reproduce all **162 files** byte-for-byte.
- Fix 3.3.10.11 core SHA-256: `content.js` `5A91E6EECAD2BF6A7C3266EA43E89BEC22392F7DDCAE691C6185F04B7437FAA2`; `manifest.json` `8BE4F258F1BAD887A691044C2329DD980E4907E5B89CAD4D9633110E5956BFF7`.

## Fix 3.3.10.12 isolated resume context

- Follow-up Edge evidence showed two distinct outcomes: one 3.3.10.11 trace stored the generated safe-resume prompt as its user request and ended incomplete; another raw `继续执行` trace ran ten Agent steps and completed in the background while the visible page still became unusable. No native Edge crash record was created.
- Manual DeepSeek requests are no longer rewritten. The page, conversation history, and durable trace retain the exact user prompt such as `继续任务`.
- The compact, DSML-sanitized checkpoint is now used only as the internal Agent task prompt after the normal DeepSeek turn has produced the initial tool execution.
- Historical tool execution objects are not replayed into the new Agent loop. Only current-turn executions are passed, eliminating a second object/history path into page state.
- The durable trace is created from the raw request rather than the synthetic checkpoint, preventing generated recovery instructions from becoming the next task identity.
- Dedicated isolation regression: **16/16 PASS**. All **33** self-test suites pass; **82 JavaScript files** pass syntax validation.
- Fix 3.3.10.12 core SHA-256: `content.js` `3AFE6900CD11DCDF66471DB0F8D7F63DEA0D4A58942F5C725F69A22A4A6B9BD8`; `manifest.json` `B2F3F42E8082C59755369875A80D6E2B4DEBD2ACC826F6DDBD3C57AE9067C598`.
## Fix 3.3.10.13 Agent context-pressure fix

- Live Edge extension storage had `memoryEnabled=false` while `systemPromptEnabled=true`, so the later page failures cannot be attributed to normal memory injection alone.
- Current ShunCode tool descriptors occupy about 37 KB in cached form; the existing manual system/tool rendering contributes about 29.2 KB of tool instructions/schema to a fully augmented manual request. This remains a secondary context cost, not the per-Agent-step root cause.
- The decisive long-Agent path is `Jz -> Nz/Pz`: every web continuation previously serialized the full cumulative execution ledger `g` into `<tool_results>` / `<tool_results_so_far>`, while DeepSeek's parent-message chain already retained previous continuation prompts.
- Server-sourced usage evidence from a real 13-step Agent rose from 15,791 to 100,497 tokens; another 9-step Agent rose from 131,749 to 177,354 and the same conversation later reached 196,407 tokens. The stable late-step growth was roughly 5K-7K tokens per step.
- Fix 3.3.10.13 adds a web-Agent result cursor. The first continuation receives the current-turn settled results; each later continuation receives only results settled since the previous web request; a nudge with no new tool result sends an empty result delta.
- The authoritative execution ledger remains cumulative in memory. `DPP_COMPLETION_GATE_31(g)`, verified-statistics checks, task-progress classification, duplicate-call protection, and tool execution history are unchanged.
- Dedicated context-pressure regression: **19/19 PASS**. A 12-turn synthetic resend fixture reduces serialized repeated-result traffic by **84.6%**.
- Fail-closed tamper probe: the 3.3.10.13 patcher exits non-zero on a modified input bundle and leaves the target hash unchanged.
- No native `msedge.exe` Application Error or matching Edge Crashpad dump was found for the observed failures, consistent with a DeepSeek renderer/tab becoming unusable under page/context pressure rather than a whole-browser process crash.
- Full health: **34/34 self-test suites PASS**; **83 JavaScript files** pass syntax validation; every shipped patcher through `apply-fix331013.py` compiles.
- Independent 3.3.10.12 -> 3.3.10.13 rebuild: **166/166 files byte-identical by SHA-256**. Core hashes: `content.js` `FB3CDB5CE056B3CE8C824A2084788DD0C0F33F7A2705AC3AD80601F6C715C827`; `manifest.json` `22AA662AE139A9D13D8B03415B49AEB5354F5EEEF6634BAF42821645070F7BC2`.

## Fix 3.3.10.14 renderer-pressure / targeted DOM scan

- The latest real failure sequence split into two classes: the old conversation was still around 200,460 server-reported tokens when the user saw server-unavailable behavior, but a newly created conversation then recorded only 4,035 tokens before the page became unusable. This rules out server context size as the sole crash mechanism.
- Live settings still show `memoryEnabled=false` and `systemPromptEnabled=true`; normal memory injection was not active during the later failure.
- No matching Edge Crashpad dump or Windows Application Error/Hang event was created. At 16:33 no new Edge renderer process was started, so switching to a new conversation was an SPA navigation inside the existing long-lived renderer rather than a renderer reset.
- The content script's shared root MutationObserver remains active on ordinary DeepSeek pages. The tool UI path previously coalesced relevant mutations with RAF but then called `C4()`, which scans recent `.ds-message` nodes (up to 24) and may TreeWalk/modify matching tool-control text. Streaming tool/DSML output can therefore turn one changed text node into repeated multi-message cleanup work.
- Fix 3.3.10.14 keeps the initial full reconciliation scan, but streaming mutation handling now gathers only `.ds-message` nodes directly touched by each mutation batch, excludes plugin-owned subtrees, caps the candidate set at four, and runs `D4/j4` only on those candidates.
- The prior 3.3.10.13 Agent result-delta fix and cumulative correctness ledger remain unchanged.
- Dedicated renderer-pressure regression: **15/15 PASS**. Under a synthetic 120-batch comparison, the maximum message-candidate work falls from `24*120` to `4*120`, an **83.3%** bound reduction.
- Full health after compatibility updates: **35/35 self-test suites PASS**; **84 JavaScript files** pass syntax validation; every shipped patcher through `apply-fix331014.py` compiles.
- Fail-closed tamper probe: a modified 3.3.10.13 `content.js` is rejected on input SHA-256 mismatch; the target hash is unchanged after the failed patch attempt.
- Independent 3.3.10.13 -> 3.3.10.14 rebuild: **168/168 files byte-identical by SHA-256**. Core hashes: `content.js` `F647EB21F644DF87898D2DF44152DBF43170C8C7A5F719497391E95E4E1FC5C5`; `manifest.json` `83D8F13274CE9C866C2D6D6A288B70C213D5A10A9BFF9ECBC2B4BE3E1A64D906`.

## Fix 3.3.10.15 web transport diagnostics / error passthrough

- The fresh real reproduction occurred before any MCP execution or inline Agent: session `9a5d60a7-...` produced server-sourced usage samples at 4,035, 8,078, 12,075 and 16,072 tokens, while the latest LevelDB log contained no new Agent trace, execution block, tool history, or parser-diagnostic write.
- The historical `dpp_mcp_parse_diag_fix2` key does contain an older `tool_call_incomplete` / `run_command` event, but no new parse error was written for this failure. Direct-XML EOF therefore remains a historical failure class, not the confirmed cause of the current incident.
- The remaining observability gap was in the ordinary completion transport wrapper: HTTP status, Content-Type, stream byte/chunk counts and parser FINISHED state were not persisted.
- Fix 3.3.10.15 records a bounded local diagnostic ring for both fetch and XHR. It stores only request/session IDs, route, request-size counts, selected descriptor names/count, HTTP status/content type, transport phase, byte/chunk or char counts, FINISHED state and short error metadata. Prompt/response bodies and authorization headers are not recorded.
- Non-2xx fetch responses and JSON fetch responses now pass through to the official DeepSeek page unchanged instead of entering the plugin SSE transformer. Successful SSE behavior is unchanged.
- Dedicated transport regression: **22/22 PASS**, including identity-preserving HTTP 503 and HTTP 200 JSON passthrough.
- Full health: **36/36 self-test suites PASS**; **85 JavaScript files** pass syntax validation; every shipped patcher through `apply-fix331015.py` compiles.
- Fail-closed tamper probe: a modified 3.3.10.14 `main-world.js` is rejected on SHA-256 mismatch and remains byte-identical to its pre-patch tampered state after the failed attempt.
- Independent 3.3.10.14 -> 3.3.10.15 rebuild: **170/170 files byte-identical by SHA-256**. Core hashes: `content.js` `7FECC173832CE58B39DCB118537CD2B42D70418418D51C0C5EC2B81EB9CB071E`; `main-world.js` `507E8A802E1367D08DDDDDB5CC94095CD9449D854AF0BF640C1C3202B97BC686`; `manifest.json` `9CE98F269394226CE8E72EDDCAF9EFE1B77C7B8BB9B9F997C942F38AFF569F33`.

## Fix 3.3.10.16 XHR terminal correlation

- Fresh post-reload evidence produced a new session (`00bc0b3a-874b-4cf9-8a4c-55e82c21c411`) and new server usage writes, but `dpp_web_response_diag_331015` remained absent. This ruled out the stale-tab explanation by itself.
- Inspection found an XHR-only correlation bug in Fix 3.3.10.15: `ro(e,t)` defined its terminal callback as `l=t=>...requestId:t.requestId...`, so the callback argument shadowed outer request metadata. The diagnostic payload had no requestId, therefore bridge validation rejected `REQUEST_TERMINAL`.
- Fix 3.3.10.16 renames the callback argument and deliberately reads `requestId` from the outer request metadata while attaching the diagnostic payload separately. Fetch logic and all MCP/Agent behavior are unchanged.
- Dedicated XHR-correlation selftest: **11/11 PASS**.

## Fix 3.3.10.17 SSE control-state trail

- Live 3.3.10.16 evidence proved the failing DeepSeek requests return HTTP 200 `text/event-stream` through XHR, end in `xhr_load`, and have `streamFinished=false` despite partial visible output.
- 3.3.10.17 records at most eight final SSE control entries: path, operation, event type, status/code-like scalar value, and an error-present boolean.
- Assistant content, reasoning, prompt text, and error message strings are deliberately excluded. Values are accepted only for status/code/finish/quasi paths and capped at 80 characters.
- Dedicated privacy/control-state selftest: **18/18 PASS**.

## Fix 3.3.10.18 pre-transport and Agent tool-shape diagnostics

- The reproduction session `ff5eb9fc-c03c-46ec-999d-aae5d095d4ad` proved three separate failure layers: two HTTP-200 SSE responses explicitly ended `INCOMPLETE` with `finish_reason=generation_err`; a later FINISHED turn entered Agent mode but `mcp_invoke` reached validation with `{}` and the following turn/nudge produced no new tool activity; finally the user's `继续` was persisted by DeepSeek's own IndexedDB with an `ASSISTANT/WIP` placeholder but produced no new DeepSeek++ transport/usage record.
- Windows Application/WER and Edge Crashpad contained no corresponding native renderer crash record, so the last symptom is treated as a page/pre-request stall rather than a proven `msedge.exe` process crash.
- `dpp_request_preflight_diag_331018` records bounded, privacy-safe stage breadcrumbs from `mw_send_hook_seen` through augmentation/content authorization/project work and `mw_transport_started`. It never stores prompt text, request bodies, or error messages.
- `dpp_agent_tool_shape_diag_331018` records tool name, argument kind, argument keys, and schema-required keys at `tool_execution_start` before validation; it never stores argument values.
- Dedicated selftest: **21/21 PASS**.

## Fix 3.3.10.25 validation

- Live-root-cause specialist regression: `43/43 PASS`.
- Full regression: `46/46 self-test suites PASS`.
- Dry health: `95` JavaScript files pass `node --check`; all patchers through `apply-fix331025.py` compile.
- Health enforces the reasoning privacy boundary: the bounded reasoning tail is classifier-only and is absent from the Agent prompt, trace constructor, and persisted Agent diagnostics.
- Clean `.24 -> .25` hash-locked patcher output is byte-identical for all six core files.
- Tampered `.24` input fails closed and leaves the manifest at `.24`.
- Independent preformal builder output from formal `.24` is `190/190` files byte-identical to the `.25` dry tree (`missing=0`, `extra=0`, `diff=0`).



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

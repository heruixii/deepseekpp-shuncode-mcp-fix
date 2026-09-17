> **⚠️ 2026-09-17 状态更新（Fix 3.3.10.36 已发布，但浏览器视觉验收失败，尚未修复）**：磁盘已部署 .36 / 1.14.0.41，GitHub 发布不变。现场 SVG 参考图任务中，扩展三次取得图像字节（18,731 B ×2、2,168 B）后，`UPLOAD_DEEPSEEK_IMAGE` 在 2–9 ms 内被后台授权门以 `runtime_message_unauthorized` 拒绝，refs=0；与图片大小无关。已核实全部拒绝子条件与日志：失败发生在**新建对话（SPA 切换进入 `/a/chat/s/<id>`）**的会话，此前同一 background 在**直接加载的旧会话**中上传成功；具体命中的子条件（`sender.url`/`tab.url` 会话不一致、`documentId` 缺失或驻留旧脚本）尚待现场验证。**不要通过删除授权检查解决。** 详见 [`docs/mcp-deepseekpp-visual-blocker-20260917.md`](docs/mcp-deepseekpp-visual-blocker-20260917.md)。
>
> **目录分离**：DSPP 全部文档、维护脚本与私有取证已从个人 `Athena计划` 工作区迁出。本仓库 `docs/` 与 `tools/` 即唯一真源；私有取证/参考图/备份位于本地 `local/`（已 `.gitignore`，不发布）。项目交接总入口：[`DeepSeekPP-Fix3-项目交接文档.md`](./DeepSeekPP-Fix3-项目交接文档.md)。

> **📖 中文安装/配置/使用指南：[`USAGE-zh_CN.md`](./USAGE-zh_CN.md)** — 暴露模式选「直接：展示全部工具」；Agent 状态条显示运行中时不要发新消息，等它结束再发「继续」。

> Current release: **Fix 3.3.10.36 / 1.14.0.41** — proactive visual workflows and a fix for false completion after reading an image. Long unregistered tool blocks no longer escape the old 20k-body/200k-text detector. Real stop/steering callbacks recover through authorized capability calls, with bounded failures instead of false completion. Visual ranking, initial/continuation guidance and a local-reference preflight are included; no permissions or native ShunCode runtime changes. **48 new workflow groups + existing suites passed; a fresh browser/model SVG task still needs verification after reload.** [Download / Release](https://github.com/heruixii/deepseekpp-shuncode-mcp-fix/releases/tag/v1.14.0-fix3.3.10.36) · [Release notes](docs/RELEASE-Fix3.3.10.36.md) · [Technical handover](docs/mcp-deepseekpp-visual-workflow-v8.md).

## Fix 3.3.10.36：主动视觉与长补丁续执行

- 参考图/SVG/UI复刻、截图转网页、图像对比等任务：主动获取真实视觉依据，不等用户额外说“用 read_image”。已附当前输入的图片可直接观察；缺本地路径时询问，不猜测或扫描私人文件。系统提示或工具注入关闭时不会被擅自开启。
- 自适应预算仍可能收缩“直接模式”的工具列表。本版提高 read_image 与相关写入工具的优先级；未暴露时使用真实 discover/describe/invoke，不凭空使用短标签。
- 读图后输出长 `<apply_patch>` 但没有执行时，不再直接 complete；按真实工具/schema重发，并同时遵守局部与整轮上限。该修复不直接执行未知 raw patch，也不恢复用户主动停止的任务。
- 成功读图不等于SVG制作完成；按要求完成生成/保存/验证，有授权渲染能力则看渲染结果复核，未做就说明。禁止冒称看图或用未经允许的trace/convert替代视觉重绘。
- 本机黑曜石已按要求整理为 dspp：4当前入口、21原笔记归档、1历史索引；保留禁止伪作画规则。只发布脱敏维护结论，不上传私人笔记库。
- 新48组视觉、22组读图、16组后台、22项原生维护、55套旧回归、14工程检查、6语法检查通过。**新版浏览器/模型端到端复测仍需用户重载后完成，不以离线测试代替。**



## 文档索引（docs/）

| 文档 | 用途 |
|---|---|
| [mcp-deepseekpp-visual-blocker-20260917.md](docs/mcp-deepseekpp-visual-blocker-20260917.md) | **最新**：.36 浏览器视觉上传阻塞取证、后台授权链、接手步骤 |
| [mcp-deepseekpp-visual-workflow-v8.md](docs/mcp-deepseekpp-visual-workflow-v8.md) | .36 实现、离线验证、部署与发布回执 |
| [RELEASE-Fix3.3.10.36.md](docs/RELEASE-Fix3.3.10.36.md) / [RELEASE-Fix3.3.10.35.md](docs/RELEASE-Fix3.3.10.35.md) | 发布说明 |
| [mcp-deepseekpp-readimage-v7.md](docs/mcp-deepseekpp-readimage-v7.md) / [readimage-v6.md](docs/mcp-deepseekpp-readimage-v6.md) / [readimage-upload-boundary.md](docs/mcp-deepseekpp-readimage-upload-boundary.md) | read_image 上传链路 v6→v7 及后台授权边界 |
| [ShunCode-read_image-图像通道-改造与维护.md](docs/ShunCode-read_image-图像通道-改造与维护.md) | ShunCode 原生 image 块维护 |
| [DeepSeekPP-read_image-自动读图-改造方案.md](docs/DeepSeekPP-read_image-自动读图-改造方案.md) / [交接排查文档.md](docs/DeepSeekPP-read_image-自动读图-交接排查文档.md) / [DeepSeekPP-图像通道-改造调查.md](docs/DeepSeekPP-图像通道-改造调查.md) | 早期读图方案与调查（历史） |
| [mcp-deepseekpp-capability-exposure.md](docs/mcp-deepseekpp-capability-exposure.md) / [manual-supersede.md](docs/mcp-deepseekpp-manual-supersede.md) / [gpu141-crash-repro.md](docs/mcp-deepseekpp-gpu141-crash-repro.md) | .33 能力暴露、手动接管、GPU141 观察（历史） |

## 历史：Fix 3.3.10.35：自动读图与覆盖安装后的恢复

- 浏览器扩展：下载本版 ZIP → 解压/备份后更新 → 扩展页面“重新加载” → 关闭旧 DeepSeek 页面并新开已登录页面。
- ShunCode 覆盖安装可能丢失原生 image 块。先运行 `python tools/shuncode-read-image-patch.py --dir "你的ShunCode内置扩展目录" --check`；**ALREADY 不写文件；仅 NEED 时保存工作、退出 ShunCode 后显式 --apply**，随后重启/重连并用非敏感小图验收。未知结构 BLOCKED 时停止，不把旧 runtime 覆盖进新安装。
- [完整恢复/回滚命令](docs/ShunCode-read_image-图像通道-改造与维护.md) · [发布技术说明与重建测试](docs/RELEASE-Fix3.3.10.35.md)。维护脚本默认只读、两文件预检、安装目录外备份、哈希和语法检查；不重置设置，不包含完整 ShunCode 安装文件或用户图片/凭据/原始浏览器日志。
- ShunCode 返回 image 块与 DeepSeekPP 上传并附加文件 ID 是两段链路；不能只凭“读取成功”文字判断识图成功。旧版本章节保留为历史，不应当作 .35 的安装补丁步骤。



> Validation: dedicated Fix 3.3.10.34 suite **24/24 PASS** (includes the poisoned-output field case); all **55 self-test suites PASS** (`.33` baseline 54/54); hash-locked `.33 → .34` patcher (`tools/apply-fix331034.py`, 5-file SHA lock + 4 fail-closed anchors, refuses dst==src), re-apply fails closed, two independent rebuilds byte-identical (**208/208**). Manifest `1.14.0.39 / 1.14.0 ShunCode MCP Fix 3.3.10.34`. ZIP `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.36.zip` (13,946,628 B) SHA-256 `ECBCB43D8F07FD8961A7E0CDA676A59E1E1CC1B5C1F592CFB3AE6FB7A90329FA`.

> Previous release: **Fix 3.3.10.33** — fixes the `.32` field failure "继续 → answers `complete` with zero tools / dies mid-task". LevelDB evidence (session `c0ba574e`, 2026-09-16) proved it was **not** a regression: every response was HTTP 200 with no DOM-fence or transport counters. Layer 1: the adaptive capability picker (`background.js` `_d/Sd/Cd`) ranks MCP descriptors purely by keyword overlap with the user prompt, so `继续` / `A` never selected `run_command` (the injected direct set was `apply_patch/find_files/get_command_output/read_image`); the system prompt still told the model to emit `<run_command>` raw bodies, the stream parser had no such tag and dropped the block as text (turn_diag `textChars` vs visible text: 347→39, 196→0, 309→0, 223→0, 268→0, 1315→57, 657→17, 790→31 on all eight failing turns). Layer 2: the `.19` temporary alias is removed only in its own `finally`; when the model consumed the same handle through `mcp_invoke` directly, the alias survived and the next direct call failed with `mcp_capability_handle_replayed`, a code outside the `.31` transport set, so the loop fell into generic nudges and died at the limit. Layer 3: `<task_complete>` with zero tool executions passed `DPP_COMPLETION_GATE_31` unconditionally. `.33` (A) adds a rank floor for core ShunCode tools (`DPP_CORE_TOOL_FLOOR_331033`: run_command +1600, get_command_output/read_files +1000, apply_patch/search_files/list_directory +700) so they survive the 5-slot adaptive cut regardless of wording; (B1) retires aliases whose capability was consumed by any `mcp_invoke`; (B2) adds handle-lifecycle codes to the transport-failure set with targeted steering ("re-discover, then invoke next turn"); (C1) detects unregistered tool tags (`DPP_UNREGISTERED_TOOL_TAG_331033`, diag `unregistered_tool_tag_331033`) and treats them as tool intent with steering that explains the tag was ignored; (C2) rejects a zero-tool `<task_complete>` on continuation prompts or when reasoning carries tool intent (`zero_tool_complete_331033`). The .25/.27 "visible final wins", .31 transport gate and .32 safe-final guard are all asserted unchanged.

> Validation: dedicated Fix 3.3.10.33 suite **53/53 PASS**; all **54 self-test suites PASS** (`.32` baseline 51/51); hash-locked `.32 → .33` patcher (`tools/apply-fix331033.py`, 5-file SHA lock + 11 fail-closed anchors), re-applying to a patched tree fails closed, two independent rebuilds byte-identical (**206/206**). Manifest: `1.14.0.38 / 1.14.0 ShunCode MCP Fix 3.3.10.33`. ZIP `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.33.zip` (13,933,248 B) SHA-256 `7A398F4FADB8DB54289EEB3F0746F276246635DB9A79E6C05D2FD3498396B795`.

> Historical release: **Fix 3.3.10.32** — stops the Agent from promoting an *announced-but-unsent* tool call to a final answer. Executing the real `content.js` functions against the failed live loop `098021bb` proved the chain: the model wrote its `run_command` plan only in reasoning and emitted a 25-character body; `DPP_TOOL_INTENT_331021` consults reasoning only when the body is empty or itself carries a clue, so no tool-intent nudge fired and `DPP_SAFE_FINAL_CANDIDATE_331021` promoted the truncated text as final (`totalTools:0`). The failure was also unobservable, because `dpp_agent_turn_diag_331021` is flushed on a 650 ms batch and the loop's `window.location.reload()` raced the un-awaited `pagehide` flush. `.32` changes only the promotion point (C): if reasoning carries tool intent, there is no `<task_complete>`, and the turn has no `result.ok===true` execution, the text is **not** promoted; the loop routes to `AGENT_LOOP_ERROR`, the trace lands as `error` (resumable) and no reload fires. (D) `DPP_DIAG_BATCH_FLUSH_ALL_331022` now returns a Promise that is awaited before reload. An unconditional reasoning fallback inside `DPP_TOOL_INTENT_331021` was tried first and rejected because it regressed fix331025/fix331027 (a visible concrete final must win over stale reasoning).

> Validation: dedicated Fix 3.3.10.32 suite **12/12 PASS**; all **51 self-test suites PASS** (`.31` baseline 50/50); the real failed trace flips promotion true → false while unrelated traces are unchanged; hash-locked `.31 → .32` patcher, tampered and double-patched input fail closed, independent rebuild tree diff **0 (203/203 files identical)**. Manifest: `1.14.0.37 / 1.14.0 ShunCode MCP Fix 3.3.10.32`. ZIP `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.32.zip` SHA-256 `7C52B0C5721CD63CC4ACA4A3DF07A986F980DD6508ACC2BE55FB7324BD100D8C`.

> Historical release: **Fix 3.3.10.31** — makes an interrupted task resumable after an MCP transport failure. Live LevelDB evidence showed `run_command` returning `ok=false / error.code=mcp_network_error` (ngrok tunnel blip); `DPP_COMPLETION_GATE_31` counted the failed execution as progress, the model's one-line “MCP disconnected, retrying” took the `final` branch of `shouldStopAfterTurn`, the trace was persisted as `complete`, and `DPP_RESUME_TRACE_CHAIN_331010` — which adopts only `error`/`stopping`/stale `running` traces and uses the newest `complete` as a watermark — refused to take over, so “继续/重试” degraded into plain chat with no tool context (three `editMessage` requests, HTTP 200, zero `turn_decision`). `.31` (a) forbids transport-class failures (`mcp_network_error`, `mcp_timeout`, `mcp_unauthorized`, `capability_expired`) from reaching `final`: `tool_transport_failure_331031` re-emits the call up to 3 times, then `tool_transport_failure_limit_331031` lands the trace in `error`; (b) restricts the resume watermark to genuinely successful runs. Validation: dedicated suite **43/43**, all **50 suites PASS**, hash-locked `.30 → .31` patcher, tamper/double-patch fail closed, independent rebuild **201/201** identical. Manifest `1.14.0.36`. ZIP (rebuilt from the frozen tree) SHA-256 `C50C507A0CD0388A868763970DBCEC2DA5FF9DFEAE20653EF1300B31502B7605`.

> Historical release: **Fix 3.3.10.30** — root-cause fix for the recurrent "页面崩溃" screen on hard refresh of an agent-heavy DeepSeek conversation. CDP capture proved the chain live: on hard refresh DeepSeek++ restores tool blocks / agent traces into React-managed `.ds-message` containers; DeepSeek's own reconciler (`su` in the fe-static bundle) then calls `Node.insertBefore` with a stale anchor, the resulting `NotFoundError` escapes to the app error boundary, and the whole page is replaced by DeepSeek's own crash screen — while the renderer process itself stays alive (no `Inspector.targetCrashed`, no new Crashpad dump; app-level "alive but crashed", which is why earlier process-level checks looked healthy). `.30` installs `DPP_DOM_FENCE_331030` in the MAIN world at `document_start`, wrapping `Node#insertBefore/removeChild/replaceChild`: only `NotFoundError` is recovered (foreign anchors append at the intended parent, already-detached removals become no-ops, mis-parented nodes are removed from their real parent, failed `replaceChild` falls back to append); every recovery is counted in a throttled `localStorage` beacon `dpp_dom_fence_diag_331030`, and all other exceptions still throw. Windows LiveKernelEvent 141 is tracked separately from this bug — no new 141 events correlate with the afternoon crash wave. User-verified fixed on the previously crash-on-refresh conversation.

> Validation: dedicated Fix 3.3.10.30 behavior suite **21/21 PASS**; all **49 self-test suites PASS**; hash-locked `.29 → .30` patcher, tampered input fails closed, independent rebuild tree diff **0 (199/199 files identical)**; only `manifest.json` + `content-scripts/main-world.js` of the five core files changed. Manifest: `1.14.0.35 / 1.14.0 ShunCode MCP Fix 3.3.10.30`.

> Previous release: **Fix 3.3.10.29** — live Fix 3.3.10.28 evidence showed the first task starting correctly, but the second task's page crashed around completion/persistence. The Agent loop itself finished cleanly (5 steps / 5 real tool actions, HTTP 200, no generation_err or Agent exception), while the extension wrote about 975 KB of Local Storage state in the short repro: ~536 KB usage history, ~252 KB Agent traces, ~131 KB tool history, ~55 KB turn diagnostics. The 15-second delayed usage flush aligned almost exactly with the large write. `.29` removes the 536 KB legacy usage array from the hot write path by writing new usage records into per-day v2 shards plus a small meta record; legacy v1 stays read-only for compatibility and is merged only on stats/history reads. Agent trace and tool-history disk budgets are also tightened from ~128 KB to ~64 KB. This reduces extension-side persistence pressure, but does **not** claim that the ambiguous Windows LiveKernelEvent 141 (which still referenced an old Aug-21 WATCHDOG dump) proves or is fixed as a GPU crash.

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

> Current release: **Fix 3.3.10.18** — closes the pre-transport observability gap around manual sends such as “继续”: privacy-safe breadcrumbs now record request stages from the fetch/XHR send hook through content-side augmentation, authorization/project-context work, and transport start. It also records Agent tool-call argument shape (keys/required keys only) before schema validation, so malformed empty calls such as `mcp_invoke {}` can be localized without storing prompt text, request bodies, or argument values.

> Previous release: **Fix 3.3.10.17** — records a privacy-safe trail of the final SSE control paths/status/code values (maximum eight entries) so HTTP-200 incomplete streams can be distinguished between explicit server failure states and silent EOF, without storing assistant text, reasoning, prompt text, or error messages.

> Previous release: **Fix 3.3.10.16** — fixes XHR transport-diagnostic correlation: the terminal callback now preserves the outer request ID instead of shadowing it with the diagnostic payload, so XHR `REQUEST_TERMINAL` events pass bridge validation and reach the persistent diagnostic ring.

> Previous release: **Fix 3.3.10.15** — makes ordinary DeepSeek completion failures observable and fail-open: HTTP error and JSON responses pass through untouched, while privacy-safe fetch/XHR diagnostics record status, content type, stream termination, byte/chunk counts, request-size delta, and exposed tool names without storing prompt/response bodies or auth headers.

> Previous release: **Fix 3.3.10.14** — reduces renderer pressure during DeepSeek streaming by scoping tool/DSML DOM cleanup to only the message nodes touched by the current mutation batch (maximum four), while preserving one initial full reconciliation scan and all tool/Agent behavior.

> Previous release: **Fix 3.3.10.13** — prevents long DeepSeek web Agents from resending the entire accumulated ShunCode tool-result history on every continuation turn. The web request carries only newly settled tool results, while the full in-memory execution ledger remains available to completion, verification, and anti-repeat guards.

> Previous release: **Fix 3.3.10.12** — isolates interrupted-task recovery from the DeepSeek page request/render path: the user prompt and trace stay unchanged, only the internal Agent receives a DSML-sanitized checkpoint, and historical tool objects are never replayed.

> Previous release: **Fix 3.3.10.10** — restores interrupted Agent checkpoints instead of restarting completed work, fixes false-positive `run_command` success and blank-final “complete” states, classifies ambiguous 120-second MCP disconnects safely, and adds an honest live status strip.

> Previous release: **Fix 3.3.10.9** — globally retires expired unclaimed Agent traces while protecting live work in other DeepSeek tabs, repairs terminal traces that retained streaming steps, and injects deterministic `list_directory` facts so the model cannot estimate unsupported totals.

> Previous release: **Fix 3.3.10.8** — closes abnormal inline-Agent lifecycles with an inactivity watchdog, terminal-state fallback, page-unload/overlap cleanup, and durable stale-trace recovery. It also aligns `run_command` with ShunCode's native Bash schema and treats command-level failure as failure instead of transport success.

> Previous release: **Fix 3.3.10.7** — stops active inline Agents before a new manual DeepSeek turn can fork the same parent-message chain, and performs one abortable retry for transient MCP HTTP 502/503/504 only on read-only verification tools; mutating commands are never replayed automatically.

> Previous release: **Fix 3.3.10.6** — safely salvages EOF-truncated DeepSeek DSML tool calls only when every parameter is complete and schema-safe, then supplies a synthetic FINISHED status so the official page does not mislabel that recovered tool turn as server unavailable.

> Current release: **Fix 3.3.10.3** — invalid-message-id recovery now performs one bounded fallback to the previous successfully used parent after the existing same-parent retry is exhausted.

> Current release: **Fix 3.3.10.2** — manual-chat page streaming now hides orphan tool/DSML closing tags before DeepSeek React renders them, while raw stream data remains available to the tool parser.

> Current release: **Fix 3.3.10.1** — malformed DSML storms are quarantined instead of aborting the turn; valid prefix text and the official response message chain are preserved.

> Current release: **Fix 3.3.10** — filters orphan DSML/tool closing-tag noise, stops repeated control-markup storms, and prevents direct-XML + legacy-DSML duplicate tool execution while preserving Fix 3.3.9 message-ID recovery.

> Current release: **Fix 3.3.9** — hardens DeepSeek response message-ID selection and adds one bounded recovery for explicit `code=0 / invalid message id`, while preserving Fix 3.3.8 Agent budgets.

# DeepSeek++ ShunCode MCP Fix 3.3.10.17

这是基于 **DeepSeek++ 1.14.0** 的稳定性优化版本，重点改善 DeepSeek 网页端通过 MCP 长时间调用 **ShunCode** 时的工具调用可靠性、连续执行能力和异常恢复行为。

> 本仓库不是 DeepSeek++ 官方分支，也不隶属于 DeepSeek 官方团队。它是在原项目基础上的个人优化与兼容性修复版本。

## 原项目与原作者

原项目：**DeepSeek++**  
原仓库：[`zhu1090093659/deepseek-pp`](https://github.com/zhu1090093659/deepseek-pp)  
原项目维护者 / GitHub 作者：**zhu1090093659**  
Chrome Web Store 发布者：**chunlinzhu666**  
原项目许可证：**Apache License 2.0**

DeepSeek++ 是一个面向 DeepSeek 网页版的开源浏览器扩展，提供 MCP、记忆、Skills、自动化、联网搜索、浏览器控制、对话导出等 Agent 工作流能力。

本仓库保留原项目归属与许可证。所有基础功能、UI、主体代码和原始设计均来自上游 DeepSeek++；本仓库主要集中于 ShunCode MCP 场景下的可靠性修复与执行策略优化。

## 本版本做了什么

### 1. MCP 工具调用解析增强

增强 DeepSeek 输出到工具调用之间的容错处理，减少因为模型生成格式轻微异常导致的调用失败，包括：

- 工具命名空间和后缀识别
- wrapper 解包
- `run_command` 参数归一化
- `apply_patch` 参数别名
- Windows 路径和反斜杠转义修复
- 非法 JSON escape 修复
- 嵌套引号、字面换行、控制字符处理
- 尾随逗号和 fenced JSON 修复
- JSON 前后夹杂说明文字时的提取
- `run_command` / `apply_patch` raw body 支持
- 保守的 EOF 自动闭合
- schema-aware 参数别名与类型转换

目标不是让解析器“猜测一切”，而是在不使用 `eval`、不放宽安全边界的前提下，提高模型工具调用的成功率。

### 2. ShunCode MCP 长任务连续执行

修复模型在长任务中执行几步后，输出类似“先测试”“下一步检查”“还需要验证”却提前结束的问题。

现在加入：

- 中间步骤语义识别
- 最多 8 次连续纠偏 nudge
- 工具真正取得进展后才重置 nudge 计数
- “继续 / 接着 / continue / go on”等短指令自动获得长任务步数预算
- 普通任务、项目任务、明确要求执行到完成的任务采用不同 step budget
- 连续重复相同工具和参数时进行 no-progress 阻断

对于“继续直到完成”一类任务，最大执行步数提升到 **36**，硬上限仍保留，避免无限循环。

### 3. Completion Gate：修改后必须验证

Fix 3.1 增加了完成门槛：

如果模型刚刚进行了文件修改、命令写入、安装、提交等操作，但之后还没有成功的读取、诊断或测试验证，就不能直接把任务标记为完成。

系统会区分：

- `mutation`：修改、写入、patch、删除、移动、安装、提交等
- `verification`：读取、搜索、诊断、状态检查、测试等
- `neutral`：无法安全归类的命令

这样可以减少“工具返回成功，所以模型直接宣布完成，但实际上没有检查结果”的情况。

### 4. 副作用命令的模糊结果保护

对于 `run_command`、`apply_patch` 等可能产生副作用的调用，如果网络在执行过程中断开，外部状态可能已经发生变化。

本版本会把这类情况标记为：

```text
externalOutcome = ambiguous
retrySafe = false
```

因此不会自动盲目重放同一条副作用命令，而是要求先检查当前状态再决定下一步。

这避免了重复写文件、重复提交、重复安装或重复执行命令。

### 5. Capability / Adaptive 修复

Fix 3.2 重点修复了 MCP capability 工作流：

- 保留 capability handle 的 **single-use / 防重放** 设计
- `mcp_discover` 即使进入旧结果 windowing，也仍然保留最小 `{capability, name, expiresAt}`
- 新 discover 结果压缩为最小 catalog，不再因为上下文压缩丢失 handle
- `handle_replayed / expired / invalid` 明确指导重新 discover
- 修复 Adaptive 路由中的中文关键词乱码
- “文件 / 目录 / 读取 / 搜索 / 修改 / 写入 / 命令 / 执行 / 运行 / 测试 / 仓库 / 提交”等中文任务可以正确参与工具排名
- “用命令写入文件”这类意图会优先提高 `run_command` 排名

实际使用中，ShunCode 当前只有约 12 个工具，因此本仓库更推荐 **Direct exposure**，直接暴露已授权工具，避免不必要的 `discover -> invoke` 中转。

### 6. 自适应工具路由

在 Adaptive 模式下，根据任务意图动态提高对应工具优先级，例如：

- 文件读取 → `read_files / search_files / find_files`
- 文件修改 → `apply_patch`
- 命令、构建、测试 → `run_command`
- Git / GitHub → `run_command` 等相关工具

同时会参考最近成功使用过的工具，并带时间衰减，减少模型反复在不合适的工具之间跳转。

### 7. 工具结果上下文压缩

长时间 Agent 任务中，完整工具输出会快速占满上下文。

本版本只压缩“发送给模型的上下文副本”，不会修改：

- 原始 MCP 返回结果
- 工具历史记录
- ShunCode 本身的输出

不同工具使用不同模型上下文预算，例如状态类、读取类、命令类分别采用不同大小上限。

### 8. 长命令交给 ShunCode `script_bridge`

Windows 下很长的 PowerShell / shell 命令不在扩展里重复实现另一套临时脚本机制。

本版本直接复用 ShunCode 自带的 `script_bridge`，减少双层转义、双层状态机和额外耦合。

### 9. 低耦合、可回滚补丁结构

优化按独立 overlay 分层：

- `apply-fix3.py`
- `apply-fix31.py`
- `apply-fix32.py`

构建顺序为：

```text
Fix 2 source
  -> Fix 3
  -> Fix 3.1
  -> Fix 3.2
  -> Fix 3.3
  -> Fix 3.3.1
  -> Fix 3.3.2
  -> Fix 3.3.3
  -> Fix 3.3.4
  -> Fix 3.3.5
  -> Fix 3.3.6
  -> health check
  -> release
```

每个补丁都采用 fail-closed 设计：如果目标 marker 不唯一或目标版本不兼容，构建直接失败，不进行模糊替换，也不留下半成品。

### 10. Fix 3.3：DeepSeek 流兼容与本地执行安全

Fix 3.3 针对 2026-09 DeepSeek 网页更新后暴露出的新稳定性问题做窄修复：

- **DeepSeek stream completion 兼容**：递归识别嵌套 `response/status=FINISHED` 与既有 `quasi_status=FINISHED`，但不会把普通正文里的 `FINISHED` 当成完成。
- **安全 EOF 恢复**：只有在没有正文、没有 reasoning、没有 response/request message id 的空 EOF 才允许额外重试一次；已经出现部分输出时绝不自动拼接或重试。
- **隐私受限的 stream 诊断**：异常只记录最近少量 SSE 结构字段（event / p / o / status），不保存正文内容。
- **UTF-8 数据完整性保护**：Windows PowerShell 5.1 下，阻止“裸 `Get-Content -Raw` 读取 UTF-8 无 BOM 文件后再写回”的危险组合，避免中文被 ANSI/GBK 误解码后永久写坏。
- **公共工具 preflight**：第一轮工具调用和 Agent 后续调用都会检查 schema 必填参数；空 `{}` 不再先发往 MCP。
- **workspace 范围恢复提示**：ShunCode 文件工具遇到 `FILE_NOT_FOUND` 时明确提示当前 workspace 边界，外部绝对路径改走 `run_command`，减少无意义重试。
- **PTY 空输出恢复**：仅对已分类为只读/验证的 `run_command`，当 PTY 明确 `exit_code=0` 且 `total_output_bytes=0` 时用 `execution=direct` 补做一次读取；修改/写入/提交类命令绝不因此重放。

这些修复不改变 capability 单次使用规则、不修改 MCP 授权语义、不复制 ShunCode `script_bridge`，也不把“流 EOF”粗暴视为成功。

## 当前版本

```text
DeepSeek++ 1.14.0 ShunCode MCP Fix 3.3.7
```

GitHub Release：[`v1.14.0-fix3.3.7`](https://github.com/heruixii/deepseekpp-shuncode-mcp-fix/releases/tag/v1.14.0-fix3.3.7)

发布 ZIP：

```text
DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.7.zip
```

SHA-256：

```text
See GitHub Release asset digest / local Get-FileHash output
```

## 推荐 ShunCode MCP 配置

对于当前这套 ShunCode MCP：

```text
Transport: Streamable HTTP
Execution Enabled: On
Execution Mode: Auto
Prompt Exposure / Exposure Mode: Direct
Connect Timeout: 10000
Request Timeout: 120000
Discovery Timeout: 20000
Max Result Bytes: 128000
Max Tool Count: 32
```

由于 ShunCode 工具数量较少，推荐使用 **Direct**。Adaptive 仍然可用，但没有必要为了十几个工具额外引入 capability 中转。

## 安装

1. 下载最新 Release ZIP。
2. 解压到固定目录。
3. 打开 Edge / Chrome 的扩展管理页面。
4. 开启开发人员模式。
5. 选择“加载解压缩的扩展”。
6. 选择解压后的扩展目录。
7. 打开 DeepSeek 网页并配置 MCP。

如果更新的是同一路径下的 unpacked 扩展，只需要在扩展管理页点击“重新加载”，然后对 DeepSeek 页面执行强制刷新即可。

## 验证情况

最终 Fix 3.3.6 已经过以下验证：

- MCP parser / schema：**17/17 PASS**
- Fix 3 policy：**19/19 PASS**
- DeepSeek 网页执行策略：**21/21 PASS**
- continuation helpers：**11/11 PASS**
- continuation flow：**6/6 PASS**
- Fix 3.1 Agent / completion / retry：**31/31 PASS**
- Fix 3.2 capability / adaptive：**17/17 PASS**
- Fix 3.3 已知问题修复：**46/46 PASS**
- Fix 3.3 真实 SSE parser 集成：**8/8 PASS**
- Fix 3.3.1 `event: close` compatibility：**12/12 PASS**
- Fix 3.3.2 Safe DOM compatibility：**21/21 PASS**
- Fix 3.3.3 Agent stability / storage pressure：**29/29 PASS**
- Fix 3.3.4 manual-chat tool storm guard：**76/76 PASS**
- Fix 3.3.5 empty-stream / fresh-PoW retry：**16/16 PASS**
- Fix 3.3.6 long-task page/storage stability：**21/21 PASS**
- 全部 JS 语法检查：**64 个 JS PASS**
- Python overlay 编译：**PASS**
- fail-closed 验证：**PASS**
- 从干净基线重建后文件哈希完全一致：**PASS**
- 隔离 Edge unpacked 扩展加载 / Service Worker：**PASS**

更详细的测试记录见 [`FIX3-TEST-REPORT.md`](./FIX3-TEST-REPORT.md)。

## 与上游的关系

本仓库的目标不是取代 DeepSeek++，而是针对 **DeepSeek Web + ShunCode MCP** 的特定工作流做稳定性增强。

如果你不使用 ShunCode，或者不需要长时间、多步、文件/命令密集型 Agent 工作流，优先使用上游官方版本：

https://github.com/zhu1090093659/deepseek-pp

如果你使用的是：

```text
DeepSeek Web
+ DeepSeek++
+ Streamable HTTP MCP
+ ShunCode
+ 长时间连续 Agent 任务
```

那么这个版本主要解决的就是这条链路里的解析、路由、连续执行、结果压缩、异常恢复和完成验证问题。

## 致谢

感谢 DeepSeek++ 原作者 / 维护者 **zhu1090093659** 提供开源项目与完整的浏览器 Agent 基础能力。

感谢原项目 Chrome Web Store 发布者 **chunlinzhu666**。

本仓库中的 DeepSeek++ 原始代码及其衍生部分遵循上游 **Apache License 2.0**。本仓库的优化代码在不改变上游版权归属的前提下随项目一并发布。

## License

本仓库基于采用 **Apache License 2.0** 的 DeepSeek++ 项目修改。

详见 [`LICENSE`](./LICENSE)。


## Fix 3.3.1 SSE close compatibility

- Recognizes DeepSeek Web `event: close` as a normal terminal event only when the associated payload contains no explicit failure evidence.
- Keeps bare EOF incomplete; `FAILED`, `error`, `aborted`, `timeout`, and similar close payloads are not accepted as success.
- Adds a production-parser regression fixture for the observed `ready -> update_file -> hint -> close` sequence.
- Keeps Fix 3.3 empty-stream retry, partial-stream safety, MCP behavior, UTF-8 guard, workspace routing, and PTY recovery unchanged.


## Fix 3.3.2 Safe DOM compatibility

DeepSeek 2026-09 网页更新新增了页面环境/扩展冲突错误边界。Fix 3.3.2 不改 MCP、Agent continuation、stream parser 或授权语义，只在 content capability 注册层启用安全 DOM 集：

- 保留 `runtime-state`、`main-world-bridge`、`mutation-hub`、`tool`、`inline-agent`、`chat-runtime`。
- 暂停 `theme`、`token-speed`、`multimodal`、`export`、`history`、`project`、`background`、`pet` 等非核心页面增强，避免直接改写 DeepSeek React 管理的侧栏/对话 DOM。
- `floating-chat.js` 继续用于其他网站，但通过 manifest `exclude_matches` 不再注入 `chat.deepseek.com`。
- 3.3.1 的 SSE `event: close` 兼容、Fix 3.3 UTF-8 / workspace / PTY / preflight 保护全部保持不变。
- 隔离 Edge + DevTools 协议实测：页面刷新后 0 Runtime exception、0 console error/warning，高风险 DPP DOM 节点不存在，扩展 Service Worker 显示 3.3.2。

## Fix 3.3.3 Agent stability / storage pressure

针对长工具链任务（特别是“读取 Obsidian 笔记并继承任务状态”）出现的页面失稳，3.3.3 修复了已由 Edge LevelDB WAL 直接证实的状态放大问题：

- Agent streaming / reasoning / tool-detected 中间态仅更新内存与 UI，不再持续写整份 trace 历史。
- 完成 step 每 4 步保存一次恢复 checkpoint；最终完成、错误、手动停止仍强制持久化。
- `dpp_inline_agent_traces` 采用 256 KiB 软预算，始终保留最新 trace，超预算时优先淘汰最旧记录。
- `deepseek_pp_tool_history` 保持逐工具审计持久化，但历史总预算收紧到 256 KiB。
- ShunCode `detail` 与 `output` 如果严格解析为同一 text payload，只保存/展示/回传模型一次；结构化 artifact / skill / memory 输出不会被折叠。
- Agent continuation 增加 Obsidian/vault 配置优先发现规则：Windows 下先读取 `%APPDATA%\obsidian\obsidian.json` / `.obsidian`，避免先递归扫描整盘。
- 真实失败 trace 离线测量：19 个工具结果从 76,691 B 降至约 51,513 B（-32.8%）；结合 checkpoint cadence，该故障链的 trace 写放大估算下降约 77.6%。
- 不改变 capability anti-replay、MCP 授权、mutation retry、Completion Gate、Fix 3.3.1 stream terminal 和 Fix 3.3.2 Safe DOM 语义。

## Fix 3.3.4 Manual-chat tool storm guard

针对一次真实 `manual_chat` 回复在约 11 秒内疯狂生成 `run_command` 的问题，Fix 3.3.4 增加同步熔断与后台安全网。Edge LevelDB 证据显示，最新保留的 100 条调用全部来自同一 request/message，均因 `tool_authorization_call_limit` 被拒；由于单授权 hard limit 为 128，这一回复实际至少尝试了约 228 次工具调用。命令不是半截流式误解析，而是完整闭合的 `</run_command>`，并出现 `Out-String -Width` 数值指数级膨胀。

- `manual_chat` 单回复最多 8 个工具、同一种工具最多 6 个；第 7 个同类或第 9 个混合工具同步熔断，后续调用不进入授权、MCP、history 或 DOM。
- 熔断后的回复不会自动接续 inline Agent，避免“异常回复 -> Agent 再继续”的二次风暴。
- 重复 call id 会被本地丢弃；已允许调用的 chunk 可以完成，新的 blocked call chunk 不再进入 external-payload 路径。
- 后台授权再加独立安全网：`manual_chat/sidepanel_chat=24`、`test=8`，`agent_run/automation` 保持既有 128，不削弱正常长 Agent。
- `tool_authorization_call_limit` 被归类为终止型 tool-storm 错误，不再建议 refresh authorization。
- `run_command` 本地 sanity guard 会阻止明显失控的 PowerShell `Out-String/Out-File -Width` 超大值；合理值保持正常。
- 3.3.3 的 256 KiB trace 预算增加 read-time migration，并由 runtime-state 启动主动触发：旧超限 trace 不再等待下一次 Agent 才清理。
- 合成 228-call 真实形态回放：前 6 个同类调用允许、后 222 个在执行层之前阻断；40 个 `agent_run` 连续调用模拟全部不受影响。
- 不改变 MCP server 配置、capability anti-replay、Completion Gate、mutation retry、SSE close 兼容和 Safe DOM 语义。

## Fix 3.3.5 Empty-stream recovery / fresh PoW retry

针对 `DeepSeek response stream ended before completion (the response was interrupted).` 的剩余真实空流问题，Fix 3.3.5 把历史记录按终止形态拆开处理，而不是把所有 SSE EOF 当成同一问题。

- 17:42 的 `ready -> update_file -> hint -> close` 属于旧的 `event: close` 终止识别问题，已由 Fix 3.3.1 修复。
- 17:52、18:51 以及 20:00–20:02 的记录没有可解析的终止 marker；其中 20:00–20:02 连续三次均为“一个初始 `run_command` 成功后，第 0 个 continuation 收到 0 文本、0 reasoning、0 message id，然后 EOF”。这是真正的 empty-stream recovery 类问题。
- 这三次失败使用不同的新 anchor assistant message（24 / 28 / 32），因此不是简单复用同一个 stale parent。
- 旧实现只在 `BR()` 外层创建一次 auth + PoW header，随后 `HR()` 的第二次 HTTP 恢复尝试复用同一请求对象。3.3.5 保留最多两次尝试，但第二次会重新读取当前 auth 并重新创建 PoW challenge/answer/header。
- 如果首轮已经收到正文或 reasoning 后发生网络异常，不再自动重放，避免重复提交部分回复。
- 增加隐私安全的 stream diagnostics：attempt、HTTP status、content-type、raw bytes、chunk count、fresh-PoW；不记录 prompt、Authorization、token 或 PoW 内容。
- 如果两次仍为空，继续 fail closed，仍报告 interrupted，不把裸 EOF 当成功。
- 新专项回放：**16/16 PASS**；包括空流重试成功、网络错误前置恢复、partial stream 禁止重放、两次空流有界失败及诊断隐私检查。
- `event: close`、Safe DOM、Agent storage、tool-storm guard、UTF-8、PTY、Completion Gate 和 capability anti-replay 行为全部保持。

## Fix 3.3.6 Long-task page / storage stability

Fix 3.3.6 targets a separate long-task failure mode where MCP/Agent execution can finish successfully while the DeepSeek page itself becomes unstable. The diagnosis came from real Edge extension LevelDB and browser process state.

- A real long run completed **12 steps / 21 tools in ~130 seconds**, followed by another **6 steps / 6 tools in ~65 seconds**. Both Agent traces were `complete`; there was no new renderer Crashpad dump and Edge processes remained responsive.
- The 12-step trace itself was only about **97 KB** (largest step about **15 KB**), so current Agent trace compaction is not the dominant failure source.
- `deepseek_pp_tool_history` had grown to about **555 KB / 100 records**, even though the current source contains a 256 KiB trim path. This exposed an MV3 update risk because previous Fix releases changed only `version_name` while `manifest.version` remained `1.14.0`. Fix 3.3.6 bumps the real package version to **`1.14.0.1`**, forcing Edge to replace the background service worker.
- `dpp_tool_execution_blocks` was about **729 KB**, including one historical block with **410 executions / ~543 KB** from the old tool-storm incident. Previous code had only a 30-day / 100-block limit and no byte budget.
- Tool execution blocks now have a **256 KiB total budget**, **64 KiB per block**, and **64 executions per block**. Oversized legacy records are compacted on read and newly written blocks are compacted before persistence.
- Background startup now explicitly migrates old tool history through the existing 256 KiB budget.
- The inline-Agent MutationObserver still watches the official DeepSeek message so it can recover if React removes/replaces the Agent container, but it now ignores mutations generated inside `.dpp-agent-container` itself and coalesces relevant maintenance to one animation frame.
- Reasoning streaming is now animation-frame coalesced, matching the already-throttled visible text stream; step/loop completion explicitly flushes pending reasoning so final content is not lost.
- Long-task capacity is not reduced: no lower step/tool budget was introduced.
- New regression: **21/21 PASS**, including a synthetic 410-execution block, total/single-block byte budgets, self-mutation filtering, React-removal detection, reasoning flush, startup history migration and real MV3 version bump.

## Fix 3.3.7 uploaded-file continuation / JSON response handling

- Real failure evidence: an Agent turn spawned from a message with one uploaded file returned HTTP 200 with `Content-Type: application/json`, 89 response bytes and one chunk instead of SSE. Fresh-PoW retry had already succeeded at the transport layer.
- The uploaded file contents were not copied into the Agent trace; the failure path came from the original `ref_file_ids` being preserved into synthetic Agent continuation turns.
- Synthetic Agent turns now send `ref_file_ids: []`; normal user upload requests are unchanged and still carry their explicit file IDs. Conversation history is inherited through `parent_message_id`.
- HTTP 200 JSON completion responses are no longer parsed as SSE. Only safe `code/message` fields are surfaced; arbitrary JSON/body fields are not logged.
- Explicit JSON/business responses are non-retryable and do not consume a second fresh-PoW attempt. True empty-stream/network failures keep the bounded Fix 3.3.5 retry.
- Regression: 28/28 PASS. Real MV3 version is `1.14.0.2`.

## Fix 3.3.10.25 validation

- Live-root-cause specialist regression: `43/43 PASS`.
- Full regression: `46/46 self-test suites PASS`.
- Dry health: `95` JavaScript files pass `node --check`; all patchers through `apply-fix331025.py` compile.
- Health enforces the reasoning privacy boundary: the bounded reasoning tail is classifier-only and is absent from the Agent prompt, trace constructor, and persisted Agent diagnostics.
- Clean `.24 -> .25` hash-locked patcher output is byte-identical for all six core files.
- Tampered `.24` input fails closed and leaves the manifest at `.24`.
- Independent preformal builder output from formal `.24` is `190/190` files byte-identical to the `.25` dry tree (`missing=0`, `extra=0`, `diff=0`).


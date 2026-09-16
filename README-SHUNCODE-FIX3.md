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

# DeepSeek++ 1.14.0 — ShunCode MCP Fix 3

Fix 3 基于 `DeepSeek++ 1.14.0 ShunCode MCP Fix 2`，目标是提高 DeepSeek 网页端连续调用同一套 ShunCode MCP 的可靠性，同时把新增逻辑控制在低耦合、可回退、可测试的边界内。

原 Edge 商店版、Fix 1、Fix 2 不需要修改或删除。

## 设计原则

- **低耦合**：新增执行策略集中在独立的 `fix3-policy.js`；background 加载失败时通过 optional chaining 回退到 Fix 2 行为。
- **不复制已有能力**：超长 Windows 命令继续交给 ShunCode 自带的 `script_bridge`，Fix 3 不再造第二套临时脚本机制。
- **不丢完整结果**：压缩只发生在“送给模型的上下文副本”，原工具结果/现有历史链保持原流程。
- **副作用工具不盲重试**：`run_command`、`apply_patch`、写入/删除/提交等操作，即使网络错误标记为 retryable，也不自动重跑。
- **fail-closed 构建**：补丁标记不唯一或新版 bundle 不兼容时，构建器直接失败，不做模糊替换，也不会留下半成品。

## Fix 3 完成的优化

### 1. 结果分层与动态上下文预算

DeepSeek 网页 inline-agent 原本已有“最近 4 个结果较完整、较老结果窗口化”的结构，Fix 3 在该结构上增加按工具类型的预算，而不是另建结果存储系统：

- status / health / check：约 6 KB
- read / list / find / search / fetch：约 12 KB
- run / exec / shell / build / test：约 16 KB
- 其他工具：约 9 KB

background 自有聊天链也使用独立策略做模型侧压缩；完整结果不因该压缩被原地改写。

### 2. 安全自动重试

只读型工具在以下条件同时成立时最多自动重试一次：

- 执行失败；
- provider 明确返回 `retryable=true`；
- 不属于 `externalOutcome=ambiguous`；
- 工具名属于 read/list/find/search/get/status/fetch/inspect 等只读类别；
- 不属于 run/exec/apply_patch/write/create/delete/update/commit/push 等副作用类别。

DeepSeek 网页正文调用链和扩展自身聊天链都覆盖该策略。

### 3. Adaptive 工具路由

继承 Fix 2 的 `5 tools / 14 KB schema` adaptive hard cap，并新增：

- 根据任务文字对文件读取、修改、命令、Git 类工具增加意图权重；
- 最近成功使用的工具获得短时权重（10 分钟衰减窗口）；
- 不修改用户明确设为 direct 的暴露语义。

为避免把 chat/session ID 硬耦合进 minified selector，这里使用短时 recent-success bias，而不是重写整个工具目录状态模型。

### 4. 两阶段参数编译

在 Fix 2 schema compiler 基础上增加：

- `cmd -> command`
- `timeout / timeoutMs -> timeout_ms`
- `working_directory / workingDirectory -> cwd`
- schema default 值
- string -> number/integer/boolean 安全规范化

别名只有在 **目标字段明确存在于 MCP schema** 时才转换；不支持的自定义字段保持原样，不猜参数。

### 5. 错误分类与精简反馈

模型侧错误会带较短的 `stage/action`：

- `format_or_schema`
- `authorization`
- `mcp_transport`
- `mcp_tool`
- `loop_guard`
- `tool_runtime`

完整底层诊断仍走原诊断日志体系，避免用长堆栈污染模型上下文。

### 6. 动态工具步数

DeepSeek 网页 inline-agent：

- 普通任务：12 步
- 代码/文件/项目/修复/构建/测试任务：24 步
- 明确“继续直到完成 / until done”类任务：36 步

扩展自身聊天链采用同一档位思想，硬上限为 40。

### 7. 无进展循环保护

网页 inline-agent 对连续相同的 `tool + 参数` 做稳定序列化检测；连续重复达到阈值后返回 `dpp_fix3_no_progress`，要求模型换工具或参数，而不是继续真实执行。

background 策略层采用 `allow, allow, allow, block, block, stop` 的更严格保护。


### 7.1 连续任务不中断热修

Fix 3 续跑判定新增两类保护：

- 识别“先测试 / 下一步检查 / 需要用命令写入 / 还需要验证”等明显中间态表达；
- 当原始任务明确要求“继续直到完成 / 做完为止 / 不要中断 / until done”时，要求模型通过 `<task_complete>` 明确结束。

同时修复原先 `maxNudges: 8` 未真正生效的问题：现在最多允许 **8 次连续无工具纠偏**；模型一旦真正执行工具，纠偏计数立即清零。若连续 8 次仍不给工具调用或完成标记，则安全停止，避免空转。

### 8. 超长命令处理

不重复实现临时 `.ps1`。ShunCode 本身已经能够使用 `script_bridge` 处理超长 Windows 命令，Fix 3 明确委托该层，减少重复文件、清理逻辑和新故障点。

### 9. 健康检查与诊断

原 MCP “测试连接”后台结果额外带 Fix 3 健康信息，包括：

- policy 是否加载；
- MCP cache 是否 ready；
- 工具数；
- 是否有 run_command / apply_patch；
- run_command schema 基础检查；
- 长命令处理策略；
- 结果压缩策略。

离线统一健康检查：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\health-check.ps1
```

诊断导出同时包含 Fix 2 parserEntries 和 Fix 3 策略状态；不会主动记录 command/patch/token/password 参数值。

### 10. Fail-closed 自动构建器

从 Fix 2 兼容基线生成 Fix 3：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\build-fix3.ps1 `
  -Source "D:\path\to\Fix2" `
  -Destination "D:\path\to\Fix3" `
  -ZipPath "D:\path\to\Fix3.zip"
```

内部流程：复制基线 -> 全量内存匹配 -> 应用 overlay -> 自测 -> 健康检查 -> ZIP。

若 bundle 标记发生变化，`apply-fix3.py` 会退出且不修改源；`build-fix3.ps1` 会删除不完整的目标目录和 ZIP。

> 这不是对任意未来 minified 版本进行模糊 patch。新版本结构变化时必须先确认兼容标记；拒绝构建比生成一个看似可加载、实际不可靠的版本更安全。


## Fix 3.1 必要稳定性优化

Fix 3.1 不扩大 UI 或 MCP 协议面，只修复长任务执行中的高价值边界：

- **Ambiguous 副作用保护**：当 `run_command` / `apply_patch` 等副作用调用出现 `externalOutcome=ambiguous` 时，模型侧错误明确变为 `action=verify_before_retry`、`retryable=false`、`retrySafe=false`，要求先检查真实状态，避免重复执行已经可能成功的操作。
- **Completion Gate**：成功修改后，如果之后没有成功的读取、诊断或测试验证，模型即使输出 `<task_complete>` 也不会立即结束；必须先验证最终状态。
- **短“继续”继承长任务额度**：`继续`、`接着`、`continue`、`go on` 等短续跑请求按 36 步预算处理，避免复杂任务因为下一轮只输入“继续”而退回 12 步。
- **有效进展才清零纠偏计数**：失败工具和 loop-guard 拦截不再刷新 no-tool nudge 额度；只有真实成功的工具结果才清零连续纠偏计数。
- **工具效果分类**：`apply_patch` 等明确修改工具直接标记 mutation；`read_files`、`get_diagnostics` 等标记 verification；`run_command` 根据命令内容保守区分修改/验证/中性。
- **独立低耦合 overlay**：新增 `tools/apply-fix31.py`。构建流程为 Fix 2 -> Fix 3 -> Fix 3.1；任一 marker 不匹配时 fail-closed。

新增 `fix31-agent-selftest.js`，覆盖工具效果分类、completion gate、ambiguous 重试保护、短“继续”预算、有效进展判断，以及修改→验证的多轮状态模拟。


## Fix 3.2 Capability / Adaptive 路由修复

Fix 3.2 保留 capability handle 的单次消费与防重放设计，不把句柄改成可重复使用。修复的是围绕它的两个可靠性问题：

- **Capability window 保留**：`mcp_discover` 即使成为第 5 个以前的旧工具结果并进入 `windowed:true`，仍保留最小 `{capability,name,expiresAt}` 列表；长 description 不带入旧窗口，避免上下文膨胀。
- **新 discover 也做最小 catalog 压缩**：模型始终能看到 capability handle，同时明确标注 `singleUse=true`。
- **Replay / expired 指向正确恢复动作**：`mcp_capability_handle_replayed/expired/invalid/descriptor_stale` 统一分类为 `mcp_capability -> rediscover_capability`。
- **修复中文 Adaptive 路由乱码**：早期 `routeBonus()` 中中文关键词曾被编码成乱码；现改为 ASCII 源码中的 Unicode escape。`文件/目录/读取/搜索/修改/写入/命令/执行/运行/终端/构建/测试/仓库/提交/分支` 均可正常影响工具排名。
- 对“用命令写入文件”这类中文意图，`run_command` 额外获得 command + edit 组合加权，实际 12 工具缓存回放中排名第一并进入 5-tool direct 集。

### ShunCode 推荐 Exposure

ShunCode 当前只有 12 个工具。对于需要持续读/改/测/命令执行的项目任务，**推荐将该服务器的 Prompt Exposure / Exposure Mode 设置为 `Direct`**。这样 12 个已授权 ShunCode 工具都直接可用，不需要 `mcp_discover -> mcp_invoke`。

`Adaptive` 仍受支持；如果继续使用默认 `5 tools / 14 KB`，大 schema 会受到上下文预算限制。Fix 3.2 已修复中文路由和 capability window，但 Direct 对当前 ShunCode 工作流更稳定。

新增 `fix32-capability-selftest.js`，覆盖 capability window、string/object discover output、坏 JSON fail-safe、中文/英文路由、replay 恢复动作。

## Fix 3.3 DeepSeek Stream / UTF-8 / Workspace 稳定性修复

Fix 3.3 保持在独立 `apply-fix33.py` overlay 中，不重写 Fix 3/3.1/3.2 的策略模块。主要修复：

- DeepSeek SSE `FINISHED` 递归兼容，支持状态事件嵌套在 BATCH/对象中；只接受精确 status path + `FINISHED`，防止正文误判。
- 空流 EOF 的单次安全重试；任何部分正文、reasoning 或 response/request id 都禁止自动重试。
- 最近 8 个 stream 结构事件的隐私受限诊断，不持久化正文。
- 公共工具执行入口 + Agent wrapper 双层 schema preflight，阻止 `{}` 参数先进入 MCP。
- Windows PowerShell 5.1 UTF-8 round-trip guard，阻止裸 `Get-Content -Raw` + 文本写回组合。
- `FILE_NOT_FOUND` 的 workspace-scope 恢复提示。
- PTY `exit 0 + output 0` 只对 verification 类命令安全切 `direct` 重试；mutation 类严格禁止。
- `WriteAllText/WriteAllLines/AppendAllText/...` 纳入 mutation 分类，避免安全重试误伤。

Fix 3.3 仍采用 exact-marker + SHA-256 compatibility gate，任何目标函数不匹配都会 fail-closed，且不会留下部分修改。

## 当前自动测试

- Parser / schema：17 项 PASS
- Fix 3 policy：19 项 PASS
- DeepSeek 网页主链策略：21 项 PASS
- 连续任务语义识别：11 项 PASS
- 连续任务控制流：6 项 PASS
- Fix 3.1 Agent / completion / retry：31 项 PASS
- Fix 3.2 Capability / Adaptive：17/17 PASS
- Fix 3.3 已知问题修复：46/46 PASS
- Fix 3.3 SSE parser 集成：8/8 PASS
- Fix 3.3.1 SSE close：12/12 PASS
- Fix 3.3.2 Safe DOM：21/21 PASS
- Fix 3.3.3 Agent stability / storage pressure：29/29 PASS
- Fix 3.3.4 Manual-chat tool storm：76/76 PASS
- Fix 3.3.5 Empty-stream / fresh-PoW retry：16/16 PASS
- Fix 3.3.6 Long-task page/storage stability：21/21 PASS
- 诊断隐私测试：PASS
- 全部 JS 语法（64 个 JS）：PASS
- UTF-8 manifest / EN / ZH locale：PASS
- 自动重建：PASS
- 不兼容基线零写入：PASS
- 构建失败半成品清理：PASS
- 手工完成版与自动重建版核心运行文件哈希一致：PASS

详细结果见 `FIX3-TEST-REPORT.md`。

## Edge 加载

1. 打开 `edge://extensions/`。
2. 开启“开发人员模式”。
3. **先禁用**商店版 DeepSeek++，不要卸载。
4. 选择“加载解压缩的扩展”。
5. 选择：`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`。
6. 刷新 `https://chat.deepseek.com/`。
7. 确认 ShunCode MCP ready，然后测试长 PowerShell、带中文/空格路径、读取→修改→验证的连续任务。

如果 Edge 报相同扩展 ID 冲突，不要删除商店版；需要另做独立 ID + 配置迁移版本。

## 当前验证边界

自动测试和静态/重建测试已完成。Fix 3.3 已使用独立 Edge profile + remote debugging 验证 unpacked 扩展真实注册并启动目标扩展 Service Worker，结果 **PASS**。仍无法在隔离 profile 中自动完成需要用户 DeepSeek 登录态的真实网页 Agent 会话，因此“已登录 chat.deepseek.com 的最终 E2E”保留为人工冒烟边界。

## Fix 3.3.1 SSE close compatibility

- Recognizes DeepSeek Web `event: close` as a normal terminal event only when the associated payload contains no explicit failure evidence.
- Keeps bare EOF incomplete; `FAILED`, `error`, `aborted`, `timeout`, and similar close payloads are not accepted as success.
- Adds a production-parser regression fixture for the observed `ready -> update_file -> hint -> close` sequence.
- Keeps Fix 3.3 empty-stream retry, partial-stream safety, MCP behavior, UTF-8 guard, workspace routing, and PTY recovery unchanged.


## Fix 3.3.2 Safe DOM compatibility

DeepSeek 新前端会在页面结构被扩展修改后进入自己的错误边界，并提示“页面崩溃可能与浏览器插件对页面内容的修改有关”。本次修复采用 capability-level 降级而不是重写 React/DOM 逻辑：

- 核心链路保留：runtime state、MAIN-world bridge、共享 mutation hub、tool UI、inline Agent、chat runtime。
- 非核心高风险页面增强暂停：theme、token speed、multimodal、export、history organizer、project sidebar、background、pet。
- floating chat 对 DeepSeek 域名禁用，对其他网站保持原行为。
- 不修改 MCP server 配置、工具授权、Direct Exposure、stream terminal、Completion Gate 或 side-effect retry 规则。
- `tools/apply-fix332.py` 使用 3.3.1 整文件 SHA-256 + UX block SHA-256 双门槛；不匹配时 fail-closed。
- 独立 3.3.1 -> 3.3.2 重建与 trial **122/122 文件 SHA-256 一致**。

## Fix 3.3.3 Agent stability / storage pressure

- 直接解析 Edge LevelDB WAL 证实：长 Agent 任务会反复整块写入约 360–385 KiB 的 `dpp_inline_agent_traces` 与约 385–403 KiB 的 `deepseek_pp_tool_history`。
- Streaming / reasoning / tool-detected 中间态改为 memory-only；step checkpoint 每 4 步一次，final/error/stop 仍强制落盘。
- Agent trace 与 tool history 分别使用 256 KiB 软预算，保留最新状态并优先淘汰最旧历史。
- 对 ShunCode text-wrapper 的 `detail` / `output` 做严格等价去重，同时用于 trace、Agent DOM、模型 continuation 和后台 tool history；结构化输出保留。
- Obsidian/vault 定位优先读取 `%APPDATA%\obsidian\obsidian.json`，再进入已确认 vault，避免整盘递归发现工具风暴。
- 真实失败 trace：76,691 B -> 51,513 B（-32.8%）；结合 6 次 -> 2 次 checkpoint/error 写入，估算写放大下降 77.6%。
- `tools/apply-fix333.py` 对 3.3.2 content/background/manifest/locale 使用整文件 SHA-256 门槛，任何不匹配均 fail-closed。
- 当前 3.3.2 -> 3.3.3 独立 rebuild 与 trial：124/124 文件 SHA-256 一致。

## Fix 3.3.4 Manual-chat tool storm guard

- Live LevelDB evidence: one `manual_chat` request produced at least ~228 `run_command` attempts; the newest 100 retained history rows were all `tool_authorization_call_limit` within ~11.2 s.
- The calls were complete XML tool blocks, not partial-stream replays. Their PowerShell commands alternated D-drive enumeration variants while `Out-String -Width` exploded to pathological values.
- Content-side synchronous circuit breaker: max 8 tools per manual response / max 6 per tool name, before `x1/i2`, authorization, MCP execution, history, or DOM.
- Background defense-in-depth: manual/sidepanel grants max 24 call ids, test grants 8, agent/automation remain at 128.
- Stormed responses do not auto-start inline Agent. `tool_authorization_call_limit` is terminal (`stop_tool_calls_and_summarize`) rather than `refresh_authorization`.
- PowerShell `-Width` sanity guard blocks absurd values while allowing normal widths.
- Oversized legacy inline-agent trace arrays are trimmed under the existing storage lock, and runtime-state startup proactively triggers the migration.
- New regression: 76/76 PASS. Full prior regressions remain PASS.

## Fix 3.3.5 Empty-stream recovery / fresh PoW retry

- 历史上 `event: close` 误判（17:42）与真正无 marker 的空 SSE（17:52、18:51、20:00–20:02）是两类问题；前者继续由 3.3.1 处理。
- 20:00–20:02 连续三次失败均发生在成功的初始工具之后，continuation 仍为 0 text / 0 reasoning / no message id；三个 anchor assistant message 分别为 24 / 28 / 32。
- 旧 BR/HR 流只创建一次 auth + PoW，再在两次 HTTP attempt 间复用。3.3.5 的第二次 attempt 重新生成当前 auth 与 PoW request material。
- Partial-output transport failure 不再自动 retry；只有完全无输出、无 request/response message id 的请求可进入一次有界恢复。
- 增加 privacy-safe stream diagnostics：attempt/httpStatus/contentType/bytes/chunks/freshPow。
- 16/16 专项回放 PASS；两次空流上限不增加，不会形成新的请求风暴。

## Fix 3.3.6 Long-task page/storage stability

- Real logs show long Agent runs can complete normally (12 steps / 21 tools; 6 steps / 6 tools) while the page UI becomes unstable, with no new Edge renderer crash.
- `manifest.version` is now `1.14.0.1` (not only a `version_name` change), so MV3 background code is forced through a real update cycle.
- Background startup trims legacy tool history to the existing 256 KiB budget.
- Tool execution block persistence adds 256 KiB total / 64 KiB per block / 64 executions per block and migrates legacy oversized blocks on read.
- The inline-Agent observer ignores its own subtree mutations, still detects official React removal of the Agent container, and coalesces maintenance to animation frames.
- Reasoning streaming is animation-frame coalesced and force-flushed at step/loop completion.
- New suite: 21/21 PASS.

## Fix 3.3.7 uploaded-file continuation

- Synthetic Agent follow-up turns no longer re-attach stale `ref_file_ids` from the original user upload.
- Normal upload requests still preserve file IDs.
- HTTP 200 JSON is treated as a business/application response, with privacy-safe code/message extraction instead of SSE parsing.
- JSON responses do not trigger fresh-PoW replay; true empty streams still do.
- New suite: 28/28 PASS.

## Fix 3.3.8 long Agent budget

- Automated continuation budgets are now 88 steps minimum, 96 for project/file/fix tasks, and 128 for explicit continue/until-done tasks.
- The nudge cap remains 8 and existing tool-storm / authorization safety limits are unchanged.

## Fix 3.3.10.25 validation

- Live-root-cause specialist regression: `43/43 PASS`.
- Full regression: `46/46 self-test suites PASS`.
- Dry health: `95` JavaScript files pass `node --check`; all patchers through `apply-fix331025.py` compile.
- Health enforces the reasoning privacy boundary: the bounded reasoning tail is classifier-only and is absent from the Agent prompt, trace constructor, and persisted Agent diagnostics.
- Clean `.24 -> .25` hash-locked patcher output is byte-identical for all six core files.
- Tampered `.24` input fails closed and leaves the manifest at `.24`.
- Independent preformal builder output from formal `.24` is `190/190` files byte-identical to the `.25` dry tree (`missing=0`, `extra=0`, `diff=0`).



## Fix 3.3.10.30

**MAIN-world DOM fence for the refresh crash.** On hard refresh of an agent-heavy conversation, DeepSeek++ restores tool blocks / agent trace UI into DeepSeek's React-managed `.ds-message` containers while DeepSeek's own reconciler is also updating them; the anchor node Drift makes DeepSeek's `insertBefore` throw `NotFoundError`, and the uncaught exception becomes the app-level "页面崩溃" screen. `.30` installs `DPP_DOM_FENCE_331030` at `document_start` in the MAIN world: it wraps `Node#insertBefore`, `Node#removeChild` and `Node#replaceChild` so a `NotFoundError` (and only that error) recovers in place instead of crashing the app — foreign anchors fall back to append at the intended parent, removals of already-detached nodes become no-ops, and removals of nodes attached elsewhere are removed from their real parent. Every recovery bumps a throttled diagnostic beacon at `localStorage["dpp_dom_fence_diag_331030"]` (counts + lastAt). Fence is idempotent (`__dppFence331030`), zero-cost on the non-error path (single try/catch), and covered by `fix331030-dom-fence-selftest.js`.

## Fix 3.3.10.31

Root cause, proven from the extension LevelDB WAL (`dpp_inline_agent_traces`,
`dpp_agent_turn_diag_331021`, `dpp_web_response_diag_331015`): when the MCP
transport drops, the tool call returns a *structured* failed result
(`result.ok === false`, `result.error.code === "mcp_network_error"`) instead of
throwing. Nothing in the agent loop treated that as a non-result, so:

1. the failed execution was folded into the cumulative results array;
2. the completion gate only asks "is there a tool result", never "did it
   succeed", so a model reply such as "MCP is temporarily disconnected, retrying"
   resolved to the `final` branch;
3. the trace was persisted as `status: "complete"` even though the last step ran
   no tools and every tool in the run had failed;
4. `DPP_RESUME_TRACE_CHAIN_331010` only accepts `error` / `stopping` / expired
   `running` traces, and treats the newest `complete` as a watermark - so the
   mislabelled run both failed to qualify and blocked everything behind it.

The visible symptom was that "continue" / "retry" produced a verbal
acknowledgement and then stopped: those turns never entered the agent loop at
all (three `editMessage` responses returned HTTP 200 with zero `turn_decision`
records).

Fix, both halves required:

- **Completion gate** - a transport-class failure in the current step can never
  resolve to `final`. It re-steers the model to re-issue the same tool call, and
  after `DPP_TRANSPORT_RETRY_MAX_331031` (3) consecutive transport failures the
  loop stops through `oe`/`se`, which routes to `AGENT_LOOP_ERROR` and therefore
  persists `status: "error"` - a state the resume gateway can pick up.
- **Resume watermark** - only runs containing at least one genuinely successful
  tool execution count as a completion watermark, so a mislabelled `complete`
  can no longer mask a resumable interrupted run.

Ordinary tool failures (for example a command exiting non-zero) are deliberately
left alone: they are real results and must still be allowed to finish a task.

Release-chain maintenance: extension display name in `_locales/{en,zh_CN}`,
`manifest.version_name`, and four distinct version-gate shapes across 22 legacy
suites were bumped in step.

Validation: dedicated suite 43/43; all 50 self-test suites pass (frozen .30
baseline was 49/49); hash-locked .30 -> .31 patcher upgrades cleanly and fails
closed on tampered or already-patched input; independent rebuild matches the
release tree exactly (missing=0 / extra=0 / diff=0, 201 files). Only
`content.js`, `manifest.json`, two locale files and the version-gated suites
changed.


## Fix 3.3.10.32 - announced-but-unemitted tool call promoted to a final answer

### Symptom
After a task was interrupted, sending "continue" / "retry" produced a short
verbal acknowledgement and the run ended with zero tool calls. Sometimes the
page visibly reloaded immediately afterwards and everything stopped.

### Root cause (verified by executing the shipped predicates)
The failing turn (loop 098021bb, 25-char visible text, 435-char reasoning) was
replayed through the real functions extracted from content.js:

  DPP_TOOL_INTENT_TEXT_331021(reasoning)  = true   (intent IS visible there)
  DPP_TOOL_INTENT_331021(text, reasoning) = false  (but the combiner drops it)
  DPP_SAFE_FINAL_CANDIDATE_331021(...)    != null  (so it became the answer)

DPP_TOOL_INTENT_331021 only consults the reasoning channel when the visible
text is empty or already carries a cue. The stub text scored
midstep=false / strict=false / Mz=false, so the model's explicit plan to run
run_command again was discarded, no tool_intent steering fired, and Ee()
promoted the stub to a terminal answer with totalTools:0.

A second, independent defect kept this invisible: the batched diagnostics key
dpp_agent_turn_diag_331021 is flushed only from a non-awaited `pagehide`
listener, while the inline agent loop deliberately calls
window.location.reload() (u&&_1()) once a run completes with a continuable
response message id. The reload raced the 650 ms batch and destroyed the
evidence, which is why the .31 field failure looked like "the gate never ran".

### Mechanism of the fix
Fix C  DPP_SAFE_FINAL_CANDIDATE_331021 refuses to promote a terminal answer
       when the reasoning announces a tool action, there is no <task_complete>,
       and the run has no successful tool execution to stand on. The turn then
       falls through to AGENT_LOOP_ERROR, the trace is stored as `error`
       (a resume candidate) and, because the error path returns no truthy
       value, the loop-end reload does not fire either.
Fix D  DPP_DIAG_BATCH_FLUSH_ALL_331022 now returns a promise and is awaited
       before the reload, so failing turns remain diagnosable.

Deliberately NOT changed: the loop-end reload itself is retained, per release
decision, because it predates .30 and is not the trigger of this fault.

### Why the obvious fix was rejected
Making DPP_TOOL_INTENT_331021 always fall back to the reasoning channel was
tried first and reverted: fix331025 and fix331027 both pin the opposite rule,
"a visible concrete final takes precedence over stale reasoning". The shipped
fix therefore acts only at the promotion site, where no proper terminal
decision was reached, so both rules hold at once.

### Verification
- fix331032-reasoning-intent-selftest.js: 12/12
- full regression: 51/51 (.31 baseline 50/50)
- the real failing trace flips safeFinalPromoted true -> false, while the
  unrelated transport-failure trace d1e59b46 is untouched
- tampered input and re-patching both fail closed with no output written
- independent rebuild from the frozen .31: 203/203 files, byte-identical

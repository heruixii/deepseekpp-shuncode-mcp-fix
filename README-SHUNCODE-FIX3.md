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
- 诊断隐私测试：PASS
- 全部 JS 语法（63 个 JS）：PASS
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

# DeepSeek++ Fix 3.3.10.32 现场失败根因分析与 3.3.10.33 修复方案（MCP 能力暴露）

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

- 日期：2026-09-16
- 分析对象：扩展 1.14.0.37 / Fix 3.3.10.32（Edge 解包加载 `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`）
- 证据来源：LevelDB 快照 `D:\tmp\edsnap-331032-20260916`（20:54 采集），键 `dpp_inline_agent_traces`、`dpp_agent_turn_diag_331021`、`dpp_web_response_diag_331015`、`dpp_agent_tool_shape_diag_331018`、`deepseek_pp_tool_history`，提取结果在 `D:\tmp\keys-331032\`
- 结论性质：**非 .30/.31/.32 回归**。全部 HTTP 200、无 DOM fence、无 transport 失败计数，故障链是能力暴露 + 句柄生命周期 + 完成门三层叠加。

## 1. 现场现象（会话 c0ba574e，20:05–20:14）

| loop | 用户输入 | 结果 | 工具数 | turn_diag 决策 |
| --- | --- | --- | --- | --- |
| 02f8e7f5 | 继续 | complete | 0 | `task_complete`（空 `DPP_COMPLETION_GATE_31` 放行） |
| 1eeb8389 | 继续直到任务完成 | complete | 0 | `final`（文本非空、无意图短语） |
| 61ad9dfd | A | error | 0 | 3 次 nudge 后 `generic_continuation_limit_331025` |
| 2c7896c5 | 继续 | complete | 16（7 次 `mcp_discover`，2 次失败） | 17 步后 `task_complete` |

用户侧感受：前两轮“说完成了但什么都没做”，第三轮“中途停了”，第四轮虽成功但耗时 4 分钟、反复 discover。

## 2. 根因

### 2.1 主因：`run_command` 从未进入直连工具集，`<run_command>` 标签被解析器当纯文本丢弃

- `background.js` 的自适应暴露选择器 `_d()/Sd()/Cd()` 只按**用户提示词关键词**给描述符打分，取前 5 个作为直连工具。提示词为 `继续`/`A`/`继续直到任务完成`时没有任何关键词，`fix3-policy.js` 的 `routeBonus` 也命中不了 `cmd`。
- `dpp_web_response_diag_331015` 显示本会话注入的 ShunCode 直连工具始终是 `apply_patch / find_files / get_command_output / read_image`，**没有 `run_command`**。
- 但系统提示词仍教模型输出 `<run_command>…</run_command>` 原始体。流式解析器没有注册该标签，于是整块被当文本剥掉。
- 铁证：turn_diag 记录的原始 `textChars` 与 trace 可见文本长度对比：347→39、196→0、309→0、223→0、268→0、1315→57、657→17、790→31（8 个失败回合全部如此）。模型 reasoning 中多次出现“工具调用一直解析失败”。
- 未找到 `deepseek_pp_mcp_capability_settings` 键：模式是被 `promptExposureSettings` 从 `direct` 自动切到 `adaptive`（描述符总成本 > max(28000, 2×预算)）。

### 2.2 次因：capability 句柄生命周期与 .19 临时别名脱节

- `DPPInstallAliases331019` 在 discover 后为句柄安装 `<name>:dpp331019` 别名，别名只在**自身** `execute` 的 `finally` 里移除。
- 模型若直接用 `mcp_invoke` 消费同一句柄，别名仍存活并指向已消费句柄 → 下次直连报 `mcp_capability_handle_replayed`。传输失败同样消费句柄。
- 这些错误码不在 `DPP_TRANSPORT_ERROR_CODES_331031` 中 → 无定向纠偏 → 通用 nudge → 3 次上限 → `error`。

### 2.3 三因：完成门对“零工作量”盲

- `<task_complete>` 在 `g.length===0` 时 `DPP_COMPLETION_GATE_31` 无条件放行。
- 文本被剥到仅剩几十字、又不含意图短语时，`DPP_TOOL_INTENT_331021` 返回 false，走 `final` 分支正常结束。

## 3. 3.3.10.33 修复内容

| 编号 | 文件 | 改动 | 标识 |
| --- | --- | --- | --- |
| A | `background.js` `Cd()` | 核心 ShunCode 工具排名下限：`run_command` +1600、`get_command_output/read_files` +1000、`apply_patch/search_files/list_directory` +700，确保在 5 槽自适应裁剪中存活 | `DPP_CORE_TOOL_FLOOR_331033` |
| B1 | `content.js` turn_end | 任何 `mcp_invoke` 执行完成（成功或失败）后，退役指向同一 capability 的别名 | 内联于 `DPPInstallAliases331019` 之前 |
| B2 | `content.js` | `mcp_capability_handle_replayed/expired/invalid`、`mcp_capability_descriptor_stale`、`mcp_transport_timeout` 加入传输失败集；`DPP_TRANSPORT_STEERING_331031` 新增第三参数 code，句柄类错误给出“重新 discover 后下一轮立即 invoke”的定向纠偏 | `DPP_HANDLE_ERROR_CODES_331033`、`DPP_STEP_TRANSPORT_CODE_331033` |
| C1 | `content.js` shouldStopAfterTurn | 检测未注册工具标签 `<name>…</name>`（name ∈ ShunCode 工具名或 `mcp_t_*` 前缀，且不在注册集/别名集）→ 视为 tool_intent，记录 `unregistered_tool_tag_331033` 诊断，纠偏文本前置说明“标签被忽略、需先 mcp_discover” | `DPP_UNREGISTERED_TOOL_TAG_331033`、`DPP_UNREGISTERED_TAG_STEERING_331033` |
| C2 | `content.js` 完成门 | `<task_complete>` 且本 loop 零工具执行时，若提示词为续行（继续/continue/…直到完成）或 reasoning 含工具意图 → 拒绝，转 nudge；达上限则 `zero_tool_complete_limit_331033`（可恢复 error） | `DPP_ZERO_TOOL_COMPLETE_BLOCK_331033` |

保留不变：.25/.27 “可见具体 final 优先于陈旧 reasoning” 规则、.31 传输失败门、.32 安全 final 守卫（新套件均有断言）。

## 4. 工程产物与验证

- 补丁器：`tools/apply-fix331033.py`（`.32 → .33`，5 文件 sha256 锁定，10 个 content 锚点 + 1 个 background 锚点 `sub_once` fail-closed；自动 bump 26 个既有 selftest 版本门与 locales）。
- 新套件：`fix331033-capability-exposure-selftest.js`，6 组 53 断言（构建完整性、排序下限模拟、标签检测、句柄码、零工具完成、现场文本复现）。
- 干跑目录 `D:\tmp\DeepSeekPP-Fix331033-dry`：`node --check` 4 核心脚本通过；全量 selftest **54/54**（.32 基线 51/51）。
- 版本：manifest `1.14.0.38`，version_name `1.14.0 ShunCode MCP Fix 3.3.10.33`。

## 5. 未打补丁前的配置缓解

侧边栏 MCP → ShunCode 服务器：模式 `adaptive` → `direct`，或固定 `run_command / get_command_output / read_files / apply_patch`。

## 6. 现场验证建议（发布后）

1. 重新加载扩展，关闭旧 DeepSeek 标签，新建会话。
2. 输入 `继续` 类无关键词提示，确认 `web_response_diag` 注入工具含 `run_command`。
3. 观察 turn_diag 不再出现 `textChars` 远大于可见文本的回合；若出现 `unregistered_tool_tag_331033`，检查下一轮是否成功 discover+invoke。
4. 零工具 `task_complete` 应被 `zero_tool_complete_331033` 拦下。

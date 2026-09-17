# Fix 3.3.10.43 首次现场复盘（2026-09-17 22:45–23:52，会话 `79391779`，loops `a9fb4dae` / `ff65a7a1` / `e162a6bf`…）

- 取证：`D:/tmp/edsnap-331043-verify-20260918-0022`（扩展 LevelDB 21 键 + `chat.deepseek.com` 页面 localStorage），补充快照 `D:/tmp/edsnap-pre44-20260918-0235`（00:52–01:10 的第二次任务）。
- 结论：**.43 的目标达成——`read_image` 图像块进入视觉通道，模型真的“看到了”并产出了 SVG；但 ShunCode 仍被自动降级为 adaptive（`descriptorCount 20`），且 DeepSeek 限流对 Agent 不可见。两项都在 .44 修。**

## 1. .43 核心修复：有效

| 证据 | 值 |
|---|---|
| 22:45 之后所有 `read_image`（23:16 / 23:17 / 23:34 / 23:38，12 张 11–29 KB） | `capture → upload_start → upload_ok → request_refs(warnings 0) → request_ack` |
| loop `ff65a7a1`（23:37–23:41，「继续」，11 步 / 12 次执行 / 10 ok） | 第 9 步 reasoning 给出真实画面描述（“4 standing figures + 1 duck… white coat, black thigh-high…”），随后 `apply_patch` 写出 `svg-out/index.html`（46,900 B，259 `<path>`，51 `data-step`，无 `<image>`） |
| `unexecuted_work_limit_331036` / `unregistered_tool_tag_331033` | 0 |
| preflight 96 行 / tool_shape 64 行 | 全部干净 |

## 2. P1：descriptorCount 20 = ShunCode 被降为 adaptive

### 2.1 现象

`dpp_web_response_diag_331015`（`descriptorNames` 只保留前 12 条）：

| 时间 | descriptorCount | names[9:12] | 路径 |
|---|---|---|---|
| 09-17 09:05 / 09:40, 09-18 00:55:05 | **24** | `apply_patch, find_files, read_files`（服务器顺序） | 手动聊天（`rawBodyChars == augmentedBodyChars`，`vz()` 不套 policy） |
| 09-17 23:04 起、09-18 00:53–01:07 全部 Agent 请求 | **20** | `apply_patch, read_files, read_image`（评分排序，`find_files` 消失） | Agent（`sz()`：`promptExposureSettings` → `_d()`） |

20 = 9 内置 + **8 个 adaptive 槽** + 3 个 `local:mcp_capability` 目录项。

### 2.2 根因（用 live 代码复算）

`fix3-policy.promptExposureSettings`：

```
enabled = descriptors.filter(execution.enabled !== false)      // 内置工具也在内
total   = Σ promptDescriptorCost(d)
if (total <= max(64000, adaptiveMaxPromptBytes*2)) return settings
// 否则：每个没有“显式字符串 mode”的 MCP 服务器 → adaptive
```

| 组成 | 成本 |
|---|---|
| ShunCode 15 工具（真实 tools/list） | **49,240 B** |
| 内置 9 工具 zh-CN（memory_save/update/delete, web_search/fetch, artifact_create/bundle_create, skill_draft_create, memory_import_preview） | **17,319 B**（en 17,451） |
| 合计 | **66,559 B > 64,000** |

.43 把触发线从 48,000 提到 64,000 时只对照了 ShunCode 自身的 49,240，漏掉了内置工具。内置工具与暴露模式无关（direct/adaptive 都注入），把它们计入一个“只能靠压缩 MCP 服务器来降低”的预算没有意义。

### 2.3 为什么“UI 显示直接”没救回来

`chrome.storage.local` 里**没有** `deepseek_pp_mcp_capability_settings` 键。侧边栏下拉框的 `exposureMode` 是 `settings.servers[id]?.mode ?? 'direct'`——显示「直接」只是默认值，用户从未改过下拉框，所以 .42 的“显式 mode 字符串才受尊重”守卫看不到任何字符串。要让守卫生效，需要在下拉框实际选一次「直接」（触发 `SET_MCP_CAPABILITY_SERVER_EXPOSURE` 落盘）。.44 不依赖这一点：直接不再把内置工具计入。

### 2.4 .44 之后的预期

Agent 请求 `descriptorCount = 24`（9 + 15），`names[9:12]` 回到服务器顺序 `apply_patch, find_files, read_files`，无 `local:mcp_capability` 项。（之前手记里写的 27 = 9 + 15 + 3 是错的：direct 模式下 `_d()` 不注入目录项。）

## 3. P2：Max Result Bytes 仍是 128000

`deepseek_pp_mcp_servers` 中 ShunCode `limits.maxResultBytes = 128000`（updatedAt 23:38:46，09-18 01:06 仍为 128000）。UI 侧 `McpPage` 的 `Max Result Bytes` 输入框只做 `Number.isInteger(r) && r > 0` 校验、**无上限**，但只有点击表单的 **保存** 才经 `UPDATE_MCP_SERVER` 写入；7,000,000 从未落盘，说明当时没有保存（或保存被表单其他校验错误打断）。不是代码缺陷，.44 不改；文档改为“修改后必须点保存，并在服务器详情确认”。

## 4. P3：限流（`finish_reason=rate_limit_reached`）对 Agent 不可见

| 时间 | msgId | 现象 |
|---|---|---|
| 23:40:31 / 23:40:44 / 23:41:02 / 23:41:18 | 188/190/192/194 | 313 B 的“已完成”空流（无 finish_reason 标记）→ 三次通用续跑 nudge → `generic_continuation_limit_331025`（这一段行为正确） |
| 23:42:50 / 23:43:07 / 23:51:07 | 196/198/200 | HTTP 200、`rawBodyChars 208–211`、`visibleChars 0`、`controlTrail=[{path:finish_reason, value:rate_limit_reached}]`，loop 以「JSON instead of SSE / invalid message id」或「已停止」结束 |

链路：MAIN-world `DPP_CAPTURE_SSE_CONTROL_331017` 把 `finish_reason` 记进 `controlTrail`（只进 `dpp_web_response_diag`），content 侧的 `DPP_STREAM_DIAG_FRAME_33` 只记 `p/o/v(status)`，所以 `HR()` 看到的是“空流、无 id、未完成” → 触发 .33 的空 EOF 重放（第二次请求同样被限流）→ 最终错误文案来自后续的 `invalid message id` JSON 响应。**.44**：诊断帧带 `finish`；`HR()` 对“未收到任何文本 + 流末 `rate_limit_reached`”直接抛不可重试的限流错误；`provider_terminal` 行带 `finishReason`。

## 5. P4 / P5

- 一次 MCP 503、一次 `mkdir` 参数错误（模型把闭合标签写进命令）→ 模型侧错误，重试成功。
- `tool_failed_or_truncated` 23:16:36 / 23:27:57：v7 `failed()`（`ok:false` / `isError` / `truncated`）命中后正确 `redact` 并给出提示，随后的 `read_image` 均成功；对应的执行块与工具历史已被容量轮换清除，无法区分是路径错误还是超字节上限，但两次都不是通道故障。

## 6. 快照复现步骤

```
copy "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Extension Settings\<extid>" D:\tmp\edsnap-<tag>\ext   (跳过 LOCK)
python -X utf8 D:\tmp\ldb_extract.py D:\tmp\edsnap-<tag>\ext D:\tmp\edsnap-<tag>\ext_out
```
`dpp_web_response_diag_331015[].descriptorCount / descriptorNames[9:12] / controlTrail`、`dpp_agent_turn_diag_331021[].finishReason`（.44 起）是本轮判据。

# .41 部署后裸工具标签空转复现取证（2026-09-17 20:53–20:56）

快照 `D:/tmp/edsnap-331041-break-20260917-2058`（20:57 取，WAL `001038.log` 2,358,995 B），live manifest `1.14.0.46 / Fix 3.3.10.41`，content.js `fabe7c7c…`（与 .41 发布一致，不是旧脚本）。仅记录枚举/计数，不含用户内容。

## 1. 现象

同一会话 `03f3f33a…`（19:53 验收通过的那条长会话，responseMessageId 已到 66），三个 loop 连续以 `unexecuted_work_limit_331036` 停止：

| loop | 时间 | 步数 | 成功 tool_call | 裸标签（errorMessage） | 结束 |
|---|---|---|---|---|---|
| `5f01d908` | 20:53:26–43 | 1 | 0 | `run_command` ×4 | unexecuted_work_limit_331036 |
| `2ce33b70` | 20:54:34–55:06 | 2 | 1 | `read_image` ×4 | unexecuted_work_limit_331036 |
| `98166842` | 20:55:17–56:07 | 4 | 3 | `read_image` ×4 | unexecuted_work_limit_331036 |

每次裸标签后都有 `visual_preflight_331036 → reemit_tool_call` 纠偏行（纠偏路径确实在跑），第 4 次触发 3 次上限停止。trace 里模型可见文本就是原样 `<read_image>\n{"path": …}`。
网络侧：窗口内 `httpOk` 全 true，仅 20:55:16 一次 `INCOMPLETE`（generation_err recovery armed，compact），不是断连。

## 2. 结论

1. **.41 的 A/B（提示词给出精确标签）在本会话无效**：模型在同一 step 内被连续告知精确标签 3 次后仍继续裸写 `<read_image>` / `<run_command>`。19:53 的单次通过不具代表性。
2. **.41 改点 C 在现场永远记不到**：`DPP_RECORD_AGENT_TURN_DIAG_331021` 用字段白名单构造行，`resolution` 不在白名单里，被静默丢弃（12 条 `unregistered_tool_tag_331033` 行 `resolution` 全为缺失）。这是 .41 的实现缺陷，离线自测只断言了调用参数、没断言落盘结果。
3. 测试环境违反了 §4 测试规矩：沿用了 66 条消息的长会话；但三次全灭 + 20:53 首轮连 `run_command` 都裸写，说明不只是会话过长。

## 3. 建议（待用户裁定，未实施）

- **.42 方案 D**（任务书里推迟的行为变更）：解析层把裸 ShunCode 标签别名到唯一 `mcp_t_*_${base}` 匹配的注册工具后直接执行（只在唯一匹配时；有歧义仍走纠偏），并把 `alias_executed_331042` 记入 turn_diag。这是唯一不依赖模型听话的修法。不涉及授权检查。
- 顺带修 C：把 `resolution` 加进 turn_diag 白名单。
- 复测前按 §4：重载扩展 → 彻底关闭旧 DeepSeek 标签页 → **新会话**。

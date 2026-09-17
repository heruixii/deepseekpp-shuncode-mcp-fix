# DeepSeek++ Fix 3.3.10.33 现场"继续只跑一会就中断"分析与 3.3.10.34 修复

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

- 日期：2026-09-16 深夜
- 对象：扩展 1.14.0.38 / Fix 3.3.10.33，会话 `c0ba574e`，23:12–23:18
- 证据：LevelDB 快照 `D:\tmp\edsnap-331033-20260916-2319`，提取到 `D:\tmp\keys-331033b\`（`ldb_extract.py` 已支持 cramjam 解 snappy，19 键全量可读）

## 1. 现象与时间线

| loop | 提示词 | 步数/工具 | 停止时刻 | 同刻的手动发送（preflight `mw_send_hook_seen`） |
|---|---|---|---|---|
| 3c8a0592 | （原任务） | 13 步全部 `tool_call`，run_command 直连 | 23:15:37 | 23:15:37.159 completion |
| c44629f0 | 继续 | 1 步已执行 | 23:16:08.934 | 23:16:08.934 editMessage |
| d8d496c2 | 继续 | 2 步已执行 | 23:16:44.697 | 23:16:44.695 completion |
| 74037fae | 怎么样了 | 1 步已执行 | 23:17:04 | 23:17:21.098 completion（下一条） |
| 35591b73 | 继续完成任务 | 2 步已执行 | — | — |

四个 loop 的 trace 均为 `status=stopping / error="已停止"`。该状态唯一来源是 `r1()`（Agent 停止函数），由 `DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107` 在 `bZ()`（手动请求增强入口）中调用：**Agent 运行中用户又发了一条消息 → 扩展按 .33107 设计放弃当前 loop**。停止时刻与手动发送毫秒级吻合。

## 2. 结论
- **不是扩展缺陷，不是 .33 回归**：所有步骤 HTTP 200，`run_command` 已进直连集（web_response_diag 显示 `apply_patch / read_files / run_command`），无 `unregistered_tool_tag`、无传输失败、无 nudge。
- 用户在每步 10–20 秒的等待期内反复发「继续」，每发一次打断一次，形成"只执行一会就中断"的观感。
- 扩展侧的可改进点：中断原因只显示「已停止」，用户无法区分"自己打断"与"任务出错"。

## 3. 顺带发现的真实缺陷（.34 修复）

### E. `run_command` 假失败
`DPP_NORMALIZE_RUN_COMMAND_RESULT_33108` 用正则扫描**整个结果文本**（header + 命令输出）找 `status=failed` / `exit_code=N`。本次命令在 grep 扩展自身源码，输出里含这些字样，3 次 `status: completed / exit_code: 0` 的执行被标为 `run_command_failed`（23:15:57、23:16:38、23:17:04）。不会中断任务，但会让模型走弯路、误导用户。

### F. 手动打断不可见
无 turn_diag 记录，trace 只写「已停止」。

## 4. 3.3.10.34 改动

| 编号 | 位置 | 改动 |
|---|---|---|
| E | `content.js` | 新增 `DPP_RUN_COMMAND_HEADER_331034` / `DPP_RUN_COMMAND_STATUS_331034`：只解析 `--- OUTPUT BEGIN ---` 之前的 header（严格 `status: X\nexit_code: N` 形式，兼容 JSON 转义），无标记时才退回旧的全文扫描 |
| F | `content.js` | `r1(reason?)` 接受停止原因；`DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107` 记录 turn_diag `manual_supersede_331034` 并传入本地化文案「已被你的新消息中断……等状态栏显示结束后再发“继续”可恢复」；`pagehide` 路径不变 |
| 链 | 27 个既有套件版本门、2 locales、`fix33107`/`fix33108` 两处字符串 pin 改为语义等价断言 |

保留：.31 传输门、.32 安全 final、.33 五项修复（新套件均有断言）。

## 5. 验证
- `fix331034-run-command-status-selftest.js` 24/24（含现场毒化输出复现：completed/0 + 输出含 `status=failed exit_code=9` → 仍 ok；真实 failed/2 → 仍判失败；.28 空 PTY 注解不受影响）
- 全回归 **55/55**（.33 基线 54/54）；`node --check` 通过
- `tools/apply-fix331034.py`：5 文件 sha 锁 + 4 锚点 fail-closed，拒绝 dst==src，双独立重建 208/208 零差异，对已打补丁树重复应用 fail-closed
- manifest `1.14.0.39 / 1.14.0 ShunCode MCP Fix 3.3.10.34`

## 6. 其他排查（本快照）
- `dpp_mcp_parse_diag_fix2`：8 条 `tool_call_incomplete`（9-14 至 9-16 22:25），均为模型输出在 `</run_command>` 前被截断，对应的响应 `streamFinished=true`、`FINISHED`，属模型侧提前停止；扩展已正确拒绝执行半个调用。频率低，暂不处理。
- `web_response_diag` 64 条中 63 条 HTTP 200；1 条 `httpStatus=0 xhr_error`（21:55），单次网络抖动。
- `deepseek_pp_usage_turns_v1` 仍有 536 KB 只读遗留数据（.29 设计如此），无写入压力。
- ShunCode 服务器配置：`execution.mode=auto`、allowlist `all`、暴露模式未显式设置（默认 `direct`，工具总量小不会自动降级）。

## 7. 用户侧建议
见仓库 `USAGE-zh_CN.md`：Agent 状态条显示运行中时不要发消息；中断后等状态条结束再发「继续」；暴露模式建议「直接：展示全部工具」。

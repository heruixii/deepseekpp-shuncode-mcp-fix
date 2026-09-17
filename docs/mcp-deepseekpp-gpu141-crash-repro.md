# DeepSeek++ 页面崩溃复现取证（Fix 3.3.10.29 之后）

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

- 日期：2026-09-16 14:00 前后（Windows 主机本地时间）
- 触发：用户复测报"ds 网页端不断崩溃"
- 取证产物：`D:\tmp\edsnap-331029-repro-20260916\`（LevelDB 快照）、`D:\tmp\keysnap_*.txt`（key 值导出）、`D:\tmp\analyze_leveldb.py`（WAL WriteBatch 解析器）

## 修订（2026-09-16 傍晚）：根因改判，以本节为准

- **实锤机制**：CDP 240s 现场捕获（`D:\tmp\capture.py` → `D:\tmp\hang_capture.json` / `probe_page.png`）确认页面崩溃 = 扩展恢复路径把工具块/agent 轨迹注入 React 管理的 `.ds-message` 容器，DeepSeek 前端 reconciler（fe-static `su`）`insertBefore` 锚点漂移抛 `NotFoundError` → 未捕获 → app 错误边界「页面崩溃」屏。**renderer 未死**（evaluate 探活正常、无 targetCrashed），属应用层"假活真崩"。
- 用户裁定"是扩展注入互撞"；无扩展对照（probe2，guest 态无效）终止不再补跑。
- **GPU 141 归位**：13:53 后下午崩溃波无新增 141 → 与刷新崩溃解耦，降级为机器级独立观察项；下方"结论"节（GPU 挂起定性）**作废**，保留作排查过程档案。
- **修复**：Fix 3.3.10.30 MAIN-world DOM 保险丝（`Node#insertBefore/removeChild/replaceChild`，只吞 NotFoundError 就地恢复 + 节流 beacon `dpp_dom_fence_diag_331030`），49/49 套件全绿；验证方式见桌面交接文档 §5-1。

## 结论（旧版 14:00 定性，已作废——保留存档）

软件链全绿；崩溃定性为**本机 GPU 图形栈挂起（LiveKernelEvent 141）导致标签页卡死**——与"无新 Crashpad dump、浏览器不整体重启"的观测吻合。

## 软件链证据（13:52–13:55 复现窗口，会话 c0ba574e / loop a5d1fb38）

- `dpp_web_response_diag_331015`：全部 HTTP 200、SSE FINISHED、无 errorMessage、无 generation_err。
- `dpp_agent_turn_diag_331021`（80 条）：errorName 全空；nudge → reemit_tool_call → tool_call 恢复链正常；最后一条 13:55:04 为正常 tool_call。
- `totalTokens` 42K→47K，无上下文雪崩；usage v2 分片（`v2_day_2026-09-16`）正常增长；v1 536 KB 大键仅被写 1 次（只读兼容生效）。

## GPU 证据

- Application 日志 WER Event 1001：**当天 LiveKernelEvent 141 已重复 10+ 次**（00:31 / 04:55 / 06:54 / 08:48 / 08:49 / 12:26 / 13:07 / 13:17 / 13:34 / 13:53…），P2/P3 完全相同（同一挂起引擎）。
- **13:53:07 落在 Agent 运行窗口内**（首条 usage 13:52:02，step:8 13:55:18）。
- 显示适配器：Intel UHD 31.0.101.5186（2024-01）+ RTX 4070 Laptop 32.0.15.9636（2026-04）双显卡，另有 **GameViewer / MuMu 两个虚拟显示驱动**。
- Edge 全部进程 13:50:32 启动（LevelDB 同时走 Recovering log），之后未再整体重启；Crashpad 最近 dump 仍为 2026-09-10。

## 遗留软件项（非崩溃根因，候选 .30）

`.29` 仅拆 usage 系列；仍有整值重写通道：`dpp_agent_turn_diag_331021`（17 次全量 ≈941 KB）、`deepseek_pp_tool_history`（11 次 ≈774 KB）、`dpp_inline_agent_traces`（8 次 ≈568 KB）、`dpp_tool_execution_blocks`（2 次 ≈254 KB）、`dpp_agent_tool_shape_diag_331018`（8 次 ≈130 KB）。

## 下一步

按桌面交接文档 §5 做 GPU A/B 实验：①退净 GameViewer/MuMu；②Edge 关硬件加速；③固定单 GPU。每步连续 2~3 任务验证。

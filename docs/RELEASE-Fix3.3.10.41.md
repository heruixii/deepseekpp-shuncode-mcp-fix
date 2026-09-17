# Fix 3.3.10.41（扩展版本 1.14.0.46）

2026-09-17 · 修复裸 ShunCode 工具标签导致的 `unexecuted_work_limit_331036` 空转停止：任务反复以"DeepSeek 连续 3 次明确表示要调用工具，但仍未输出可执行 tool call"结束。

## 版本

manifest `1.14.0.46` / `1.14.0 ShunCode MCP Fix 3.3.10.41`。运行时相对 .40 的改动**仅 content.js 一个文件**；`background.js`、`content-scripts/main-world.js`、`fix3-policy.js` 与权限均不变。

| 文件 | SHA-256 |
|---|---|
| content-scripts/content.js | `fabe7c7ca8283044caf31c909398f53f74d8d6be189b21d4f3a9c9463f16cb01` |
| background.js（不变） | `76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5` |
| content-scripts/main-world.js（不变） | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |
| fix3-policy.js（不变） | `c8e843c8bb49e312596dc02da0a5e20699c7e8ffa471a8879bf1168c8ce9c8c6` |

## 根因

MCP 工具在扩展内注册为 `mcp_t_<serverId>_<name>`。模型对 `run_command` 学会了用全名，但对读图始终裸写 `<read_image>`：

1. 裸名不在注册表 → `.33` 未注册标签检测器命中；
2. `.33` 纠偏文案一律叫它先 `mcp_discover` —— 可该工具**明明已在当前目录里**（tools=24）；
3. `.36` 视觉规则/重试文案又反复以**裸名** `read_image` 要求调用，从不给真实标签名；
4. 提示自相矛盾，模型空转，同一 step 内 3 次 tool-intent 纠偏后触发 `DPP_TOOL_INTENT_NUDGE_MAX_331021` 安全停止。

2026-09-17 16:00 的 5 次中断**全部**是扩展侧安全停止：窗口内 0 条 `xhr_error/abort/timeout`、0 条 `httpOk:false`、0 条 `generation_err`，**无一网络原因**。

## 修复

- **A 纠偏文案定向**：命中裸名且注册表中存在**唯一**的 `mcp_t_*_<base>` 时，文案改为"该工具已注册为 `<精确全名>`，下一轮直接用该标签调用，不要 discover"。无匹配或多匹配时保留原 discover 文案。
- **B 视觉提示带真实名**：`DPP_VISUAL_RULES_331036` / `DPP_VISUAL_RETRY_331036` 从工具目录解析 read_image 的真实 invocationName 并写入文案；解析不到时回退原文。
- **C 诊断**：`unregistered_tool_tag_331033` 新增固定枚举 `resolution: exact_hint | discover_hint | ambiguous`（仅枚举，无名字/URL）。
- **D 不做**：裸标签别名到前缀工具后直接执行属行为变更，风险是把引用文本误当调用，本版不实现。

**不触碰任何授权检查**：上传门 `DPP_REQUIRE_UPLOAD_CONTEXT_V7` 及 background.js 全文与 .40 逐字节一致。

### 两点实现说明

1. **注册名匹配不写死 serverId 段数**。用 `mcp_t_` 前缀 + `_<base>` 后缀锚定 + 唯一性校验；若写死段数，换 MCP server 时会静默退回 discover 文案（正是本次故障形态）。
2. **四处改点全部内联自包含**。`DPP_VISUAL_RULES/RETRY_331036`、`vo()`、`shouldStopAfterTurn`、`DPP_UNREGISTERED_TAG_STEERING_331033` 会被 v8 套件分别抽出单独 eval，引用外部 helper 必报 `ReferenceError`。validator 新增 `no_external_v41_ref_in_eval_regions` 固定该约束。

## 验证

- **离线**：`tools/validate-fix331041.py` **passed: true**，31 checks / 69 test processes / 56 legacy suites 全通过；新专项 `dspp-bare-tool-tag-v41-selftest.js` **34/34**；视觉 v8 **48/48**；篡改基线 / 篡改源工具 / 重复打补丁均 **fail-closed** 且不写输出；由干净 .36 基线 hash 锁链式重建两次 **228/228 零差异**，与候选逐字节一致。
- **浏览器（2026-09-17 19:53，loop `924059bb`）**：`status=complete`、5 步 5 工具，链路 `read_image`(首次 `mcp_tool_result_error`) → `run_command` → **`read_image` ok=True** → `run_command` → `task_complete`。窗口内**裸 `<read_image>` 0 次**、`unregistered_tool_tag_331033` **0 条**、`unexecuted_work_limit_331036` **0 次**（.40 时五次全中）。

### 诚实边界

- 改点 C 的 `resolution` 枚举**现场未被观测到**：模型压根没再写裸标签，该字段没有触发机会，其正确性目前仅有离线自测覆盖。
- 浏览器验收为**单任务单次**，不等于全面回归。
- 首次 `read_image` 返回 `mcp_tool_result_error`（重试即成功）已记为观察项。

## 构建

```
python tools/apply-fix331041.py --build <干净 .36 树> <新目录>
python tools/validate-fix331041.py --root <候选> --baseline <干净 .36 树> --tools tools --output <新目录>
```

builder 在 .40 builder 之上链式应用（先产出 .40 树，再打 .41 补丁），源哈希锁 `tools/fix331041-source-sha256.json`。输出目录必须不存在；基线只能用干净 .36 树。重建需 Python 3.10+ / Node 20+。

## 升级与复测

1. 下载本 Release 的 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.41.zip`（用 `SHA256SUMS.txt` 校验）；备份后更新解压目录。
2. `edge://extensions` / `chrome://extensions` **重新加载扩展**，**彻底关闭旧 DeepSeek 标签页**后新开已登录页面；目标显示版本 **1.14.0.46**。
3. 跑一个需要参考图的任务。期望：不再出现"连续 3 次明确表示要调用工具"的停止；`dpp_read_image_diag_v7` 出现 `upload_ok → refs → ack`。
4. 若仍被裸标签卡住，读 `chrome.storage.local.dpp_agent_turn_diag_331021` 中 `unregistered_tool_tag_331033` 行的 `resolution` 字段判断分支。

## 工程资料

- [.41 任务书与回执](mcp-deepseekpp-bare-tool-tag-fix41.md)
- [.36 视觉规则原始设计](mcp-deepseekpp-visual-workflow-v8.md)
- [.37–.40 链路](mcp-deepseekpp-visual-blocker-20260917.md) · [.40 发布说明](RELEASE-Fix3.3.10.40.md)
- [中文使用指南](../USAGE-zh_CN.md)

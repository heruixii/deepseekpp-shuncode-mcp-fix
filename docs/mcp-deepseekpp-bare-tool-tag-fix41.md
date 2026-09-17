# DeepSeek++ Fix 3.3.10.41 任务书：裸 ShunCode 工具标签导致 `unexecuted_work_limit_331036` 空转停止

> 状态：**待实施**（本文只含取证结论、根因、修复方案与验收门槛；未改任何运行代码）。
> 适用基线：live `D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` = Fix 3.3.10.40 / 1.14.0.45（content.js 911140 B `ddda4a9e…`，background.js 661170 B `76df1046…`）。
> 上游文档：`DeepSeekPP-Fix3-项目交接文档.md`（§7 2026-09-17T16:2x 条目）、`mcp-deepseekpp-visual-workflow-v8.md`（.36 视觉规则/前置检查）、`mcp-deepseekpp-visual-blocker-20260917.md` §9–§14（.37–.40 链路）。

## 1. 现象

2026-09-17 15:58–16:08，用户在浏览器连续发起 5 个视觉参考任务，每次都在执行若干 `run_command` 后停止，界面提示"DeepSeek 连续 3 次明确表示要调用工具，但仍未输出可执行 tool call。DeepSeek++ 已安全停止本轮……"。用户以为其中有网络原因。

## 2. 取证（快照 `D:/tmp/svg-vision-fix40-20260917-161111`，仅枚举/计数）

| loop | 结束 | 决策 | 之前成功 tool_call | 裸 `<read_image>` 次数 |
|---|---|---|---|---|
| 265aff17 | 15:59:21 | `unexecuted_work_limit_331036` | 0（裸 `<run_command>` ×4） | 0 |
| 0a410c9c | 16:01:56 | 同上 | 4 | 2 |
| 4a13371b | 16:02:48 | 同上 | 1 | 4 |
| bc169888 | 16:05:16 | 同上 | 5 | 8 |
| 888f44d3 | 16:07:49 | 同上 | 5 | 8 |

- 窗口内 **0** 条 `xhr_error/abort/timeout`、`httpOk:false`、`generation_err`、`AGENT_LOOP_ERROR`；`dpp_mw_bridge_diag_v10` 每轮 `send_hook tools=24 / bridge=true`、`run_ready`。→ **五次全部是扩展侧安全停止，无网络因素。**
- 32 条 `unregistered_tool_tag_331033`：`errorMessage=read_image` ×28、`run_command` ×4。
- 32 条 `turn_decision=visual_preflight_331036`、32 条 `tool_intent_steering decision=reemit_tool_call`。
- `dpp_read_image_diag_v7` / `dpp_upload_gate_diag_v9` 窗口内无新行：read_image 一次都没执行到，.38 上传链路未被触及（不是回归）。

## 3. 根因

1. **注册名 vs 裸名**：MCP 工具在扩展内注册为 `mcp_t_<serverId>_<name>`（例 `mcp_t_9a351af5_0998_48c5_b6be_7f0d1ee53257_read_image`）。模型对 `run_command` 学会了用全名（15 次成功执行），但对 `read_image` 始终裸写 `<read_image>`。
2. **检测器路径**（content.js `DPP_UNREGISTERED_TOOL_TAG_331033`）：裸名不在 `v`（注册表）也不在 `DPPAliases331019` → 命中 `DPP_SHUNCODE_TOOL_TAGS_331033` → 判未注册 → `shouldStopAfterTurn` 走 `visual_preflight_331036`（因为 `DPP_VISUAL_MISSING_331036` 同时为真）→ `getSteeringMessages` 发 tool-intent 纠偏。
3. **停止阈值**：`DPP_TOOL_INTENT_NUDGE_MAX_331021=3`；同一 step 内 `toolIntentNudgesInStep>=3` → `unexecuted_work_limit_331036`，文案 `DPP_TOOL_INTENT_LIMIT_331021`。
4. **提示词自相矛盾（真正要修的地方）**：
   - `DPP_VISUAL_RULES_331036` / `DPP_VISUAL_RETRY_331036`（.36 注入的视觉规则与重试提示）多次以**裸名** `read_image` 要求调用，从不给真实标签名；
   - `DPP_UNREGISTERED_TAG_STEERING_331033` 对裸 ShunCode 标签一律说"先 `<mcp_discover>{\"query\":\"read_image\"}` 再 `mcp_invoke`"，而该工具**已在当前目录里**（tools=24），模型于是在"discover"与"裸标签"之间空转 3 轮后被停。

## 4. 修复方案（.41，不触碰任何授权检查）

必做：
- **A. 纠偏文案定向**：`DPP_UNREGISTERED_TAG_STEERING_331033(locale, tag, registeredName?)` 增加第三参数。在 `shouldStopAfterTurn` 处，若命中裸名 `base` 且注册表 `v` 中存在**唯一**一个 `invocationName` 匹配 `/^mcp_t_[a-z0-9]+(?:_[a-z0-9]+){4}_${base}$/`，则文案改为"`<base>` 不是可用标签；该工具当前已注册为 `<精确全名>`，请下一轮直接用该标签调用，不要 discover"。无匹配或多匹配时保留原 discover 文案。
- **B. 视觉提示带真实名**：`DPP_VISUAL_RULES_331036(value, locale, readImageName?)` 与 `DPP_VISUAL_RETRY_331036(locale, readImageName?)`：从 `toolDescriptors`（`vo()` 的 `f`）/ 注册表 `v` 中解析 read_image 的真实 invocationName，文案中的 "read_image" 替换为 "`<全名>`（read_image）"。找不到时保持原文。
- **C. 诊断**：`unregistered_tool_tag_331033` 行新增固定枚举字段 `resolution: "exact_hint" | "discover_hint" | "ambiguous"`（仅枚举，无名字/URL）。

可选（需单独门禁，默认不做）：
- D. 解析层把裸 ShunCode 标签别名到唯一匹配的前缀工具直接执行——属行为变更，风险是把引用文本误当调用；.41 不做，先看 A/B 效果。

## 5. 实施流程（照 .37–.40）

1. `python tools/apply-fix331041.py --build D:/tmp/deepseekpp-base36 D:/tmp/deepseekpp-fix331041-<date>/candidate1`——**builder 须在 .40 builder 之上链式应用**（先 `apply-fix331040.py` 逻辑产出 .40 树，再打 .41 补丁），源哈希锁 `tools/fix331041-source-sha256.json`；基线只能用干净 .36 树 `D:/tmp/deepseekpp-base36`（仓库工作树不是合法基线）。
2. 新自测 `tools/dspp-bare-tool-tag-v41-selftest.js`：至少覆盖①裸 `read_image` + 唯一前缀注册 → exact 文案；②无注册 → discover 文案；③两个 server 都有 read_image → ambiguous；④围栏代码块内的 `<read_image>` 不触发；⑤视觉文案替换/回退。
3. `python tools/validate-fix331041.py --root <cand> --baseline D:/tmp/deepseekpp-base36 --tools D:/tmp/gh-deepseekpp/tools --output <newdir>`：沿用 .40 validator（22/67 + 4 组专项）并加入 .41 自测；reverse-strip 必须按 builder 精确补丁对反向还原。
4. 部署：冻结 live 到 `D:/tmp/DeepSeekPP-Fix331040-pre331041-<date>`，覆盖 6 个运行时文件，manifest 版本 1.14.0.46；用户重载扩展并**关旧标签开新页**。
5. 浏览器验收（用户做）：同一类参考图任务；期望 `dpp_agent_turn_diag_331021` 中不再出现 `unexecuted_work_limit_331036`，并出现 read_image 真实执行 → `dpp_read_image_diag_v7` `upload_ok→refs→ack`。
6. 文档：本文 §6 回执 + 交接文档 §7 + `README`/`docs/RELEASE-Fix3.3.10.41.md`；发布仍需用户明确授权（§4 规范）。

## 6. 回执

（待 .41 实施后填写：源/产物哈希、自测计数、部署时间、浏览器验收结果。）

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

## 6. 回执（2026-09-17 实施完成 + 浏览器验收通过）

### 6.1 产物
- live `D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` = **1.14.0.46 / Fix 3.3.10.41**，216 文件。
- `content-scripts/content.js`：**916638 B**，SHA-256 `fabe7c7ca8283044caf31c909398f53f74d8d6be189b21d4f3a9c9463f16cb01`。
- `background.js` / `content-scripts/main-world.js` **与 .40 逐字节一致**（`76df1046…` / `e63b1676…`）——本版只改 content.js。
- 回退点：`D:/tmp/DeepSeekPP-Fix331040-pre331041-20260917`（.40 冻结 215 文件）。
- 工具：`tools/apply-fix331041.py`、`tools/validate-fix331041.py`、`tools/dspp-bare-tool-tag-v41.js`、`tools/dspp-bare-tool-tag-v41-selftest.js`、哈希锁 `tools/fix331041-source-sha256.json`。

### 6.2 实施结果与方案差异
- A/B/C 均已实现；D（裸标签别名直执）**未做**，符合任务书。
- **与任务书的两处必要偏离**（均经验证）：
  1. **不写死 serverId 段数**。任务书的 `/^mcp_t_[a-z0-9]+(?:_[a-z0-9]+){4}_${base}$/` 会在换 MCP server（段数不是 5）时静默退回 discover 文案。实现改为 **`mcp_t_` 前缀 + `_${base}` 后缀锚定 + 唯一性校验**，套件内已用短/长 server id 两例覆盖。
  2. **所有改点必须内联自包含**。v8 套件会把 `DPP_VISUAL_RULES/RETRY_331036`、`vo()`、`shouldStopAfterTurn`、`DPP_UNREGISTERED_TAG_STEERING_331033` **分别抽出单独 eval**，引用外部 helper 必报 `ReferenceError`（实际踩中 4 次）。因此解析逻辑与文案均在这四处**内联展开**，`dspp-bare-tool-tag-v41.js` 仅作为单元测试与参考实现。validator 已加 `no_external_v41_ref_in_eval_regions` 固定这条约束。
- **修改了一个已发布套件**（经用户授权）：`tools/dspp-visual-workflow-v8-selftest.js` 第 84 行的字面量断言
  `DPP_VISUAL_RETRY_331036(d)` → `DPP_VISUAL_RETRY_331036(d,`。断言意图（steering 确实消费 visualMissing）不变，仅适配 B 方案新增参数。

### 6.3 验收计数（离线）
| 项 | 结果 |
|---|---|
| 新专项 `dspp-bare-tool-tag-v41-selftest.js` | **34/34** |
| `validate-fix331041.py` 总门 | **passed: true**，31 checks / 69 test processes / 56 legacy suites，零 FAIL |
| v8 视觉套件 | **48/48**（exit 0） |
| live 目录全量套件 | **56/56** |
| `node --check` 四核心 | 全通过 |
| 篡改基线 / 篡改源工具 / 重复打补丁 | 均 **fail-closed**，不写输出 |
| 独立重建两次 | 228/228 零差异，且与候选逐字节一致 |

### 6.5 浏览器实测结果（2026-09-17 19:53，快照 `D:/tmp/edsnap-331041-verify-20260917`）

**结论：通过。** 快照取自 19:56（`001036.log` 1,979,281 B），磁盘 manifest 为 `1.14.0.46 / Fix 3.3.10.41`。
诊断键 `dpp_agent_turn_diag_331021` 推进至 seq 11736、窗口覆盖 16:04:26–19:54:11，判定链确在执行。

19:53 loop `924059bb` 为 `.41` 部署后首次视觉任务：

| 验收项 | `.40`（16:00 五次） | `.41`（19:53） |
|---|---|---|
| 结束决策 | 五次全 `unexecuted_work_limit_331036` | **`task_complete`** |
| trace 状态 | error / 空转 | **complete，5 步 5 工具** |
| 裸 `<read_image>` | 28 次 | **0 次** |
| `unexecuted_work_limit_331036` | 5 | **0**（17:00 后零条） |
| read_image 真实执行 | 一次都没有 | **step2 ok=True** |

执行链：`read_image`（首次 `mcp_tool_result_error`）→ `run_command` → **`read_image` ok=True** → `run_command` → `task_complete`。

**最关键的证据**：`unregistered_tool_tag_331033` 在 17:00 之后 **一条都没有**（10 条全停在 16:04–16:07 的 `.40` 旧数据）——
模型直接用了正确的注册全名，纠偏路径根本没被触发，A/B 两个改点达到目的。

**诚实边界（未被现场验证的部分）**：
1. **改点 C 的 `resolution` 枚举现场未观测到**（全为 `None`，来自 16:0x 旧行）。因为模型压根没再写裸标签，该字段没有触发机会；
   其正确性目前**仅有离线自测覆盖**。不影响修复成立，但不能算已实测。
2. 19:53:44–57 出现 3 次 `completion_gate` + `reemit_continuation`，是完成门拦下未真正完工的收尾，属既有机制正常工作。
3. 首次 read_image 返回 `mcp_tool_result_error`（重试即成功）。若后续频繁出现首调失败，应单独立项排查。
4. 本次为单个任务的单次验收，不等于全面回归。

### 6.4 待办
- ~~浏览器验收（用户）~~ → **已于 19:53 通过，见 §6.5**。原步骤：`edge://extensions` 重新加载解压扩展 → 彻底关闭旧 DeepSeek 标签页 → 开新标签页，跑同类参考图任务。
  期望：`dpp_agent_turn_diag_331021` 不再出现 `unexecuted_work_limit_331036`；`unregistered_tool_tag_331033` 行的 `resolution` 应为 `exact_hint`；并出现 read_image 真实执行 → `dpp_read_image_diag_v7` `upload_ok→refs→ack`。
- **未发布**：未打 ZIP、未打 tag、未发 Release（需用户明确授权）。黑曜石 dspp 未同步 .41。
- **诚实边界**：以上全为离线证据。A/B 是否真能让模型改用精确标签，**必须等浏览器实测**；未测到 read_image 真实执行前，不能声称故障已修复。

### 6.6 发布回执（2026-09-17 20:1x，经用户授权）

- commit `2dec8a8` → `origin/main`；tag **`v1.14.0-fix3.3.10.41`**；Release **Latest**（draft=false, prerelease=false）。
- 附件 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.41.zip` **9,136,857 B / 140 条目**，SHA-256 `efabab74bc7e29ee41a14f65367f31b06d1ae94c9f78dd2583dd8f0005f71a11`；`SHA256SUMS.txt` 114 B。
- **端到端校验**：从 GitHub 回下载的字节 = 本地产物 = `SHA256SUMS.txt` 声明值，三者一致。
- **第三方可复现**：从仓库 clone 后哈希锁 3/3 校验通过，用 clone 里的 builder 由干净 .36 基线重建，7 个运行时文件与 live **逐字节一致**。
- 顺带修正：`.gitattributes` 补上 `tools/*-source-sha256.json` / `*-baseline-sha256.json` 的 `text eol=lf`。原先 `.json` 无规则，会被 `core.autocrlf` 转成 CRLF，**导致下游 clone 后哈希锁必失配**。
- ZIP 为发布布局（照 .40 清单），已断言**不包含** `local/` 私有取证、快照或 `.log`；发布说明不写自身 ZIP 哈希（避免自引用悡论）。
- 黑曜石 dspp **未同步 .41**。

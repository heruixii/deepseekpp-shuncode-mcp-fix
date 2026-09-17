# Fix 3.3.10.42 · 工具暴露漂移（.41 后任务仍连续中断的真实根因）

- 日期：2026-09-17 21:0x–21:4x
- 取证：`D:/tmp/edsnap-331041-break-20260917-2058`（20:57 采集），键 `dpp_web_response_diag_331015.descriptorNames`、`dpp_tool_execution_blocks.metadata.regenerateAuthorization.descriptorIds`、`dpp_agent_turn_diag_331021`、`dpp_inline_agent_traces`
- 结论性质：**.41 的 A/B 方向正确但打错了层**。模型裸写 `<read_image>` 不是"不听纠偏"，而是该工具**在那一轮根本没被注入**。

## 1. 证据：每一轮注入的 ShunCode 工具在漂

| 时间 | 注入的 ShunCode 直连工具 | 模型输出 | 结果 |
|---|---|---|---|
| 20:53:25 | apply_patch, read_files, **read_image** | `<run_command>` ×4 | run_command 不在表 → 4 次纠偏 → 停止 |
| 20:54:33 | apply_patch, read_files, **run_command**, get_command_output | `<read_image>` ×4 | read_image 不在表 → 停止 |
| 20:55:16 | 同上 | `<read_image>` ×4 | 同上 |

- 每轮只有 3–4 个 ShunCode 工具（总 16 个描述符，其余是 memory/web/artifact 等本地工具）。
- 模型每次调用的都是**上一轮还在、这一轮被裁掉**的工具。
- 离线用真实解析器（`vR`/`ct`）验证：只要工具在注册表，裸 `<read_image>` 本来就能解析（`ct()` 把唯一短名自动注册为别名）。所以任务书里的方案 D（裸名别名直执）对本故障**无效**——无处可别名。

## 2. 根因链

1. ShunCode 15 个工具描述符成本（`promptDescriptorCost`）= **35,883 B**，> `fix3-policy.promptExposureSettings` 的自动降级触发线 `max(28000, 2×14000)`。
2. 该函数把 `mode==='direct'`（含**用户显式选择的 direct**）一律改写为 `adaptive`，且 `deepseek_pp_mcp_capability_settings` 未落盘（快照无此键），用户侧看不到。`USAGE-zh_CN.md` §2.2 "只启用 ShunCode 一个服务器时不会触发" **是错的**。
3. adaptive 每轮按提示词关键词重新打分取 5 槽 / 14 KB；「继续」无关键词，`.33` 的 floor 只保 run_command/get_command_output/read_files/apply_patch…，**read_image 权重 0**；视觉提示词时 `routeBonus` 给 read_image +3500 把 run_command 挤掉——两种提示词得到两套互斥的工具表，正是表中两行的现象。
4. `.36` 视觉规则/`.41` 纠偏文案都在要求模型调用一个当前轮不存在的工具 → 3 次 tool-intent 上限 → `unexecuted_work_limit_331036`。

附带发现：`.41` 改点 C 的 `resolution` 字段被 `DPP_RECORD_AGENT_TURN_DIAG_331021` 的字段白名单丢弃，现场永不落盘（12 行全缺失）；`.41` 离线自测只断言了调用参数。

## 3. .42 改动（不触碰任何授权检查）

| 编号 | 文件 | 改动 |
|---|---|---|
| A1 | `fix3-policy.js` | 自动降级触发线 28000 → **48000**（单个 ShunCode 服务器 ~36 KB 保持全量直连） |
| A2 | `fix3-policy.js` | 仅对**未显式设置模式**的服务器自动降级；用户选了 `direct` 即尊重 |
| B1 | `background.js` | adaptive 默认/上限 5 槽 14 KB → **8 槽 24 KB** |
| B2 | `background.js` | `DPP_CORE_TOOL_FLOOR_331033` 给 `read_image` **+1000**（与 get_command_output/read_files 同级） |
| C | `content.js` | turn_diag 白名单加 `resolution`（≤40 字符串，否则 null） |
| 套件 | `fix33105`、`fix331033`、`dspp-bare-tool-tag-v41` | 字面量断言适配（详见 builder 注释）；新增 `dspp-exposure-drift-v42-selftest.js` 21 断言 |

B 是保险：即使用户主动选 adaptive 或将来工具总量真的超过 48 KB，run_command / read_image / read_files / apply_patch / get_command_output 五个也会同时留在 8 槽内（三种提示词离线验证 top-8 均含全部五个）。

## 4. 工程回执

- builder `tools/apply-fix331042.py`（链式：.36 基线 → .41 → .42；哈希锁 `fix331042-source-sha256.json`）；validator `tools/validate-fix331042.py`。
- validator：**passed:true**，22 checks / 69 测试进程 / 57 套件，零 FAIL；含 `background_is_41_plus_three_literals`、`policy_is_41_plus_two_literals`、`content_is_41_plus_whitelist_literal`、`gate_functions_unchanged`、`allowlist_unchanged`、`no_new_runtime_permissions`。
- 篡改基线 / 篡改源套件 / 重复打补丁：均 fail-closed 不写输出；独立重建两次逐字节一致。
- live `D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` = **1.14.0.47 / Fix 3.3.10.42**，217 文件（.41 216 + 新套件 1）；与 .41 相比只有 6 个运行时文件 + 版本门套件不同。live 57/57 套件通过。
- 回退点 `D:/tmp/DeepSeekPP-Fix331041-pre331042-20260917`（216 文件，与写入前 live 逐字节一致）。
- 运行时 SHA-256：background `e4dbd3a4616602772355cf37f152de47f374d3954bb6f7a700c140ed2931539f`；content `ff068127ddb3a7d4482826b4129f65ed6163293dcf3ebcc8bbe2a06c79714c21`；fix3-policy `2fb99f3deaf4d52c72e15b6741fcd2715e9dfbb6264789fc93726734af42e4ab`；main-world 与 .40/.41 一致 `e63b1676…`。

## 5. 浏览器验收（用户）

`edge://extensions` 重新加载解压扩展 → **彻底关闭旧 DeepSeek 标签页** → 新标签页、**新会话** → 跑参考图任务，中途发「继续」。
判据：`dpp_web_response_diag_331015` 每轮 `descriptorCount` 应为 **24**（9 本地 + 15 ShunCode），`descriptorNames` 含 `…_run_command` 与 `…_read_image`；`unexecuted_work_limit_331036` 不再出现；若再出现 `unregistered_tool_tag_331033`，其 `resolution` 字段应有值。

## 6. 诚实边界

- 以上全为离线证据 + 静态取证；.42 是否真让任务跑完，待浏览器实测。
- 提示词每轮多约 36 KB 工具 schema（回到「直接」模式的正常代价，`.32` 前也是如此）。
- 未实施方案 D；`.41` A/B 文案保留（工具在表时仍有用）。

# Fix 3.3.10.42（扩展版本 1.14.0.47）

2026-09-17 · 修复 **工具暴露漂移**：`.41` 后任务仍连续以 `unexecuted_work_limit_331036` 中断，真实根因是 ShunCode 工具集被悄悄从「直接」降级为「自适应」，每轮注入的工具表随提示词漂移，模型调用的总是**上一轮还在、这一轮被裁掉**的工具。

## 版本

manifest `1.14.0.47` / `1.14.0 ShunCode MCP Fix 3.3.10.42`。运行时相对 .41 改动 `fix3-policy.js`（2 处字面量）、`background.js`（3 处字面量）、`content.js`（1 处字面量）；`main-world.js` 与权限不变。

| 文件 | SHA-256 |
|---|---|
| background.js | `e4dbd3a4616602772355cf37f152de47f374d3954bb6f7a700c140ed2931539f` |
| content-scripts/content.js | `ff068127ddb3a7d4482826b4129f65ed6163293dcf3ebcc8bbe2a06c79714c21` |
| fix3-policy.js | `2fb99f3deaf4d52c72e15b6741fcd2715e9dfbb6264789fc93726734af42e4ab` |
| content-scripts/main-world.js（不变） | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |

## 根因

1. ShunCode 15 个工具描述符成本 35,883 B，超过 `fix3-policy.promptExposureSettings` 的自动降级触发线 `max(28000, 2×14000)`。
2. 该函数把 `direct`（**包括用户显式选择的 direct**）改写为 `adaptive`，且不落盘、用户不可见。文档中"只启用 ShunCode 一个服务器不会触发"是错的。
3. adaptive 每轮按提示词关键词选 5 槽 / 14 KB：「继续」→ run_command/get_command_output/read_files/apply_patch（read_image 权重 0）；视觉提示词 → read_image +3500 把 run_command 挤掉。两种提示词得到两套互斥的工具表。
4. 模型按上一轮的表调用 → 标签不在注册表 → `.33` 检测 + `.41` 纠偏 → 3 次上限停止。裸标签别名（原方案 D）对此无效：工具根本不在表里。

取证：20:53–20:56 三个 loop 注入表分别为 `[apply_patch, read_files, read_image]`（模型裸写 `<run_command>` ×4）与 `[apply_patch, read_files, run_command, get_command_output]`（模型裸写 `<read_image>` ×4 ×2）。详见 `docs/mcp-deepseekpp-exposure-drift-fix42.md`。

## 修复

- **A 暴露策略（fix3-policy.js）**：触发线 28000 → 48000（单 ShunCode 服务器保持全量直连）；仅对**未显式设置模式**的服务器自动降级，用户选 direct 即尊重。
- **B 自适应保险（background.js）**：默认/上限 5 槽 14 KB → 8 槽 24 KB；`DPP_CORE_TOOL_FLOOR_331033` 给 `read_image` +1000。三种提示词离线验证 top-8 均含 run_command / read_image / read_files / apply_patch / get_command_output。
- **C 诊断修复（content.js）**：`.41` 新增的 `resolution` 枚举被 turn_diag 字段白名单丢弃，现场永不落盘；本版加入白名单。

**不触碰任何授权检查**：上传门、allowlist、权限均与 .41 逐字节一致（validator `gate_functions_unchanged` / `allowlist_unchanged` / `no_new_runtime_permissions`）。

## 验证

- **离线**：`tools/validate-fix331042.py` **passed: true**，22 checks / 69 test processes / 57 suites，零 FAIL；新专项 `dspp-exposure-drift-v42-selftest.js` **21/21**；`fix33105` 14/14、`fix331033` 53/53、`dspp-bare-tool-tag-v41` 34/34；篡改基线 / 篡改源套件 / 重复打补丁均 **fail-closed**；由干净 .36 基线链式重建两次逐字节一致。
- **浏览器**：**尚未验收**。判据：`dpp_web_response_diag_331015.descriptorCount` 每轮 24、`descriptorNames` 同时含 `…_run_command` 与 `…_read_image`；不再出现 `unexecuted_work_limit_331036`。

### 诚实边界

- 本版发布时只有离线证据；是否真正让任务跑完待用户实测。
- 代价：每轮提示词多约 36 KB 工具 schema（回到 `.32` 之前「直接」模式的正常开销）。
- 未实施方案 D；`.41` 的纠偏文案保留。

## 构建

```
python tools/apply-fix331042.py --build <干净 .36 树> <新目录>
python tools/validate-fix331042.py --root <候选> --baseline <干净 .36 树> --tools tools --output <新目录>
```

链式：.36 → .40 → .41 → .42；源哈希锁 `tools/fix331042-source-sha256.json`。

## 升级

1. 下载本 Release 的 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.42.zip`（用 `SHA256SUMS.txt` 校验）；备份后覆盖解压目录。
2. `edge://extensions` 重新加载解压扩展 → **彻底关闭旧 DeepSeek 标签页** → 新标签页、新会话。
3. 若此前在侧边栏手动把 ShunCode 设成过「自适应」，改回「直接」。

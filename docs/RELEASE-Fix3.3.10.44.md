# Fix 3.3.10.44（扩展版本 1.14.0.49）

2026-09-18 · 修掉 .43 首次现场暴露出的两件事：**「直接」模式仍被悄悄降级**（descriptorCount 20 而非 24）；**DeepSeek 限流（`finish_reason=rate_limit_reached`）时扩展看不见限流标记**，会重放请求再以无关错误收场。

## 版本

manifest `1.14.0.49` / `1.14.0 ShunCode MCP Fix 3.3.10.44`。相对 .43：`fix3-policy.js` 1 处、`content.js` 5 处字面量；**`background.js` 与 `main-world.js` 与 .43 逐字节相同**。

| 文件 | SHA-256 |
|---|---|
| fix3-policy.js | `39915841f22a165e1cc395e17d4fdff5651050c2d70c2e3bc6291ac3b26f38c5` |
| content-scripts/content.js | `f5925d0dc269957afd9da9ab432f92c2262a41bb12d295ab22f309d26b2d57cc` |
| background.js（= .43） | `bfe776745f2ca97a439186833a8026915151b6789bf7418ab0cd5301d7c33c57` |
| content-scripts/main-world.js（= .42/.43） | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |

## 根因（.43 首次现场，2026-09-17 22:45–23:52）

详见 `docs/mcp-deepseekpp-fix43-first-run-20260918.md`。

1. **内置工具被计入 MCP 自动降级触发线。** `fix3-policy.promptExposureSettings` 把**所有**启用描述符的 `promptDescriptorCost` 求和后与 64,000 比较——包括 9 个内置本地工具（memory / web / artifact / skill / import，zh-CN 17,319 B，en 17,451 B）。ShunCode 15 工具是 49,240 B，单独低于 64,000，但 49,240 + 17,319 = **66,559 > 64,000**，于是 Agent 路径（`background.js sz()`）仍把唯一的 ShunCode 服务器从 `direct` 改写为 `adaptive`（8 槽）。现场证据：Agent 请求 `descriptorCount=20`（9 内置 + 8 槽 + 3 capability 目录），`descriptorNames[9:12]=apply_patch,read_files,read_image`（按评分排序，`find_files` 不见了）；而不走 policy 的手动聊天路径（`vz()`）同一日志里是 24 且为服务器原始顺序。
2. **UI 的「直接」从未持久化。** 侧边栏下拉框显示的「直接」只是默认值；`chrome.storage.local` 中没有 `deepseek_pp_mcp_capability_settings` 键，所以 .42 的“显式模式受尊重”守卫不生效。这不是 bug，但说明只靠“用户手选直接”兜不住。
3. **限流不可见。** 23:42:50 / 23:43:07 / 23:51:07 三次请求 DeepSeek 返回 HTTP 200 的空流，唯一标记是 `finish_reason=rate_limit_reached`（MAIN-world `controlTrail` 记到了，Agent 循环拿不到）。`HR()` 把它当成瞬时空 EOF **重放一次**（再消耗一次配额），随后又以「JSON instead of SSE / invalid message id」这种无关文案结束；用户只看到「已停止」。

## 修复

- **A** `fix3-policy.js`：`promptExposureSettings` 只对 `provider.kind==='mcp'` 且有 `provider.id` 的启用描述符求和。内置工具不受暴露模式影响、也无法通过“压缩 MCP 服务器”减少，本就不该计入。触发线仍为 64,000；`.42` 的显式模式守卫保留；两台 ShunCode 体量的服务器（98,480 B）仍会被降级。
- **B1** `content.js` 流诊断帧：解析到的 SSE 帧若带 `finish_reason`（固定枚举 `/^[a-z_]{1,40}$/`）记为 `finish` 字段；新增纯函数 `DPP_FINISH_REASON_331044` / `DPP_LAST_FINISH_REASON_331044`。诊断帧仍不复制任何正文。
- **B2** `content.js HR()`：一次**未收到任何文本**且流末标记为 `rate_limit_reached` 的尝试不再重放，直接抛出不可重试（`dppNoRetry337`）的限流错误，运行以明确的中英文限流提示结束：「DeepSeek 返回 finish_reason=rate_limit_reached……请等待几分钟后发送“继续”」。已收到部分文本的限流流仍按原样（incomplete）返回，不丢内容。
- **B3** `provider_terminal` 诊断行新增 `finishReason`（白名单字符串 ≤40）。
- **B4** 新增 `DPP_RATE_LIMIT_STOP_331044(locale)` 文案。

**不触碰任何授权检查**（validator `gate_functions_unchanged` / `allowlist_unchanged` / `no_new_runtime_permissions`；`background.js` 逐字节等于 .43）。

## 验证

- 离线：`tools/validate-fix331044.py` **passed: true**（31 checks / 73 test processes / 59 suites，零 FAIL）。新专项 `dspp-exposure-builtin-v44-selftest.js` **41/41**：从 live `background.js` 抽取真实 9 个内置描述符 + 冻结的真实 ShunCode 15 工具 schema，复现 .43 的 66,559 > 64,000 与现场 `descriptorCount 20 / names[9:12]` 形状，验证 .44 下 `_d()` 输出 24（9 + 15，无目录项、服务器原序）；`HR()` 限流单次即停、普通空 EOF 仍重放一次、部分文本不丢。篡改源锁 / 篡改基线 / 重复打补丁均 **fail-closed**；独立重建两次一致；live 59/59。
- 浏览器：**待验收**。判据：Agent 路径的 `dpp_web_response_diag_331015` 行（`augmentedBodyChars ≫ rawBodyChars` 的那些）`descriptorCount=24`，`descriptorNames[9:12]=…apply_patch, …find_files, …read_files`，无 `local:mcp_capability` 项；被限流的空回合以限流文案结束，`provider_terminal.finishReason=rate_limit_reached`，无追加 nudge。

### 建议同时做的设置（不改代码）

- 侧边栏 ShunCode → **工具暴露** 重新选一次「直接」并离开页面，让 `deepseek_pp_mcp_capability_settings` 真正落盘（.42 的显式守卫从此生效，双保险）。
- `Max Result Bytes` 若要直读大图请改 **7000000** 后**点保存**（表单只在保存时写入；现场值仍是 128000）。

## 构建

```
python tools/apply-fix331044.py --build <干净 .36 树> <新目录>
python tools/validate-fix331044.py --root <候选> --baseline <干净 .36 树> --tools tools --output <新目录>
```
链式 .36 → … → .43 → .44；源哈希锁 `tools/fix331044-source-sha256.json`。

## 升级

1. 下载 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.44.zip`（9,222,380 B，162 条目，SHA-256 `e300e53572f940c6abd4a598f2caa48780c490a65320499697e4423f956890fe`；校验 `SHA256SUMS.txt`），备份后覆盖。
2. `edge://extensions` 重新加载 → **彻底关闭旧 DeepSeek 标签** → 新会话。
3. 回退点（本机）：`D:/tmp/DeepSeekPP-Fix331043-pre331044-20260918`。

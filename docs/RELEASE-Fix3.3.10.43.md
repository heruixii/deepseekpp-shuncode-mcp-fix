# Fix 3.3.10.43（扩展版本 1.14.0.48）

2026-09-17 · 让 `read_image` 在 `include_data_uri:false` 时也能进入视觉通道；修正 .42 触发线；给模型说清两个真实失败原因。

## 版本

manifest `1.14.0.48` / `1.14.0 ShunCode MCP Fix 3.3.10.43`。相对 .42：`fix3-policy.js` 1 处、`background.js` 1 处（`Zo()`）、`content.js` 3 处字面量；`main-world.js` 与权限不变。

| 文件 | SHA-256 |
|---|---|
| background.js | `bfe776745f2ca97a439186833a8026915151b6789bf7418ab0cd5301d7c33c57` |
| content-scripts/content.js | `3774802fa96c8ba824d52dd5ee04c92b6782fdc33e3f8a3ce38ce837306803db` |
| fix3-policy.js | `368cb093b3b32a96f9e8263f23aeb1ee4a1c82ca699cc87fa28c5ffcf5da6f18` |
| content-scripts/main-world.js（不变） | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |

## 根因（.42 首次现场，loop `806d5ac7`）

详见 `docs/mcp-deepseekpp-fix42-first-run-20260917.md`。

1. **`include_data_uri:false` 丢图**：ShunCode 不管该参数都在 `content[]` 放 image 块，参数只控制 `structuredContent.data_uri`；扩展 `background.js Zo()` 只要 `structuredContent` 存在就整段丢弃 `content[]` → v7 通道 `no_image_data`。模型为绕开字节上限主动关掉该参数后，240px/500px 小图也全"只有元数据"。
2. **原图超限**：774 KB webp → base64 1.03 MB > 服务器 `Max Result Bytes=128000`。
3. **.42 触发线未生效**：真实 15 工具成本 49,240 B > 48,000（.42 估算漏了每工具 1024 B 开销）。
4. 模型最终答复"从未看到图"与其第 8 步 reasoning（`include_data_uri:true` 那次成功后明确描述了画面）矛盾。

## 修复

- **A** `fix3-policy.js`：自动降级触发线 48,000 → **64,000**。
- **B** `background.js` `Zo()`：`structuredContent` 存在时，若 `content[]` 含 `type:image` 块，以白名单字段（`type/mimeType/data`）最多 4 个复制到 `output.content`（仅当 structuredContent 自身没有 `content` 字段）。v7 `collect()` 的遍历键已包含 `content`，content.js 采集/脱敏逻辑**零改动**。
- **C** `content.js` v7 note：`no_image_data` 时直接点名"很可能是 include_data_uri:false，请用默认 true 重调"；`tool_failed_or_truncated` 时说明"超出 Max Result Bytes，先用 run_command 缩到约 600px 再读副本"。
- **D** `content.js` .36 视觉规则中英文：保持 `include_data_uri` 默认 true；大图先降采样。

**不触碰任何授权检查**（validator `gate_functions_unchanged` / `allowlist_unchanged` / `no_new_runtime_permissions`）。

## 验证

- 离线：`tools/validate-fix331043.py` **passed: true**，28 checks / 71 test processes / 58 suites，零 FAIL；新专项 `dspp-image-block-v43-selftest.js` **19/19**（含：`Zo()` 保留块 → 真实 v7 `capture()` 发出 `UPLOAD_DEEPSEEK_IMAGE`，且脱敏结果不含 base64；不覆盖 structuredContent 自有 `content`；上限 4；缺 mimeType/非字符串 data 跳过）。篡改基线 / 篡改源 / 重复打补丁 **fail-closed**；独立重建两次一致。
- 浏览器：**尚未验收**。判据：`dpp_read_image_diag_v7` 里 `include_data_uri:false` 的 read_image 也出现 `capture → upload_ok → request_refs → request_ack`；`descriptorCount` 24。

### 建议同时做的设置（不改代码）

侧边栏 ShunCode → `Max Result Bytes` 改 **7000000**（5 MB 原图 base64 后约 6.7 MB），可直读原图；暴露模式手选「直接」。

## 构建

```
python tools/apply-fix331043.py --build <干净 .36 树> <新目录>
python tools/validate-fix331043.py --root <候选> --baseline <干净 .36 树> --tools tools --output <新目录>
```
链式 .36 → … → .42 → .43；源哈希锁 `tools/fix331043-source-sha256.json`。

## 升级

1. 下载 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.43.zip`（校验 `SHA256SUMS.txt`），备份后覆盖。
2. `edge://extensions` 重新加载 → **彻底关闭旧 DeepSeek 标签** → 新会话。

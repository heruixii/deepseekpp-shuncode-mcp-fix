# .37 候选：上传授权门固定原因码诊断（未部署、未发布）

更新：2026-09-17。目标 **Fix 3.3.10.37 / 1.14.0.42**。状态：候选已构建并通过离线门禁；**未写入 live 目录、未发布 GitHub Release**。等待用户授权部署与浏览器复现。

## 背景

现场三场景（见 [visual-blocker 第 8 节](mcp-deepseekpp-visual-blocker-20260917.md)）证明 `UPLOAD_DEEPSEEK_IMAGE` 的 `runtime_message_unauthorized` 拒绝按**页面 document 实例**发生（同一 document 内旧/新会话都失败，F5 后同会话成功），但后台把 20 余种拒绝压成同一码，无法再细分。.37 只做一件事：在拒绝路径附加**固定枚举原因码 + 布尔探针**，不放宽任何检查。

## 改动清单（相对 .36，5 个运行时文件 + 55 个 selftest 版本门）

| 文件 | 变化 |
|---|---|
| `background.js` | 在 `DPP_READIMAGE_V7_BACKGROUND_BEGIN` 之前插入 `DPP_UPLOAD_GATE_DIAG_V9` 块；监听器同步 catch、异步 catch、`DPP_DISPATCH_UPLOAD_V7` 的 SN 分支共 3 处改为 `DPP_GATE_DIAG_V9(error, message, sender, DN(...), context)`。`wN/TN/EN/DN/aI/REQUIRE/ASSERT/DISPATCH` 函数体与 `xN` 白名单**逐字节不变**（validator 锁定）。 |
| `content-scripts/content.js` | v7 `upload()` 收到 `runtime_message_unauthorized` 时调用新 `gateReason(response)`：白名单字段写入既有 `dpp_read_image_diag_v7`（stage `gate_reason`），并向模型追加一条"授权拒绝，不可在当前文档内重试/缩图"的说明。 |
| `manifest.json`、两个 locale | 版本号 |

原因码枚举（响应 `reason` 与 `chrome.storage.local['dpp_upload_gate_diag_v9']` 环形 32 行）：
`sender_not_this_extension` `sender_lifecycle_not_active` `sender_url_missing` `sender_url_invalid` `sender_origin_mismatch` `sender_not_top_frame` `sender_tab_not_deepseek` `sender_no_frame_evidence` `sender_field_invalid` `policy_*` `tab_id_mismatch` `tab_url_missing` `tab_url_invalid` `tab_not_deepseek` `tab_missing` `tabs_get_failed` `ctx_frame_not_zero` `ctx_lifecycle_{none|prerender|cached|pending_deletion|other}` `ctx_document_id_missing` `ctx_tab_session_missing` `ctx_sender_session_missing` `ctx_sender_tab_session_mismatch` `conversation_changed` `command_not_allowed` `message_invalid` `unknown`。

探针字段（仅布尔/短枚举）：`frame` `lifecycle` `documentId` `tab` `tabUrl` `senderSession` `tabSession` `sameSession` `ctxSenderSession` `ctxTabSession` `ctxSameSession`。**不记录** URL、token、documentId 值、sender 对象、认证头。

## 验证

- 构建：`python tools/apply-fix331037.py --build BASE_36 NEW_OUTPUT`（哈希锁 227 文件基线 `tools/fix331037-baseline-sha256.json`，helper 锁 `fix331037-source-sha256.json`，Node 语法检查，输出目录必须不存在）。
- 门禁：`python tools/validate-fix331037.py --root CANDIDATE --baseline BASE_36 --output NEW_DIR`。本轮报告 `D:/tmp/deepseekpp-fix331037-20260917/validation4/report.json`：**16/16 检查、64/64 测试进程**（新 `dspp-upload-gate-diag-v9-selftest.js` 10 组：全部拒绝维持原判且原因码互异、异步 tab 拒绝、上传中导航、探针形状、环形缓冲并发不丢行、非上传命令不触发、成功路径无附加字段、门函数逐字节不变、content 透传与 sanitizer；v8 48 组、v7 读图 22/后台 16、原生 22、旧 55 套件全部通过）。
- 候选目录 `candidate4/`，运行时哈希：
  - `_locales/en/messages.json` `4fab76c26d1f421c3986be8a158bba3277c4e083a98744be8f0bedf48b2a9f29`
  - `_locales/zh_CN/messages.json` `35fa537ac99dcd5ec9d8bdbb44623a2bb0bf59a80d7fb674fe82c01cb4972e26`
  - `background.js` `be1eac90e0b892deb80addda168ff575fba7a475d872f2183e0974cc9cc09f6a`
  - `content-scripts/content.js` `ddda4a9ea97a4105454ab0cea3970eb35212da3c9527a4e82519937e0f4d43fe`
  - `fix3-policy.js` `c8e843c8bb49e312596dc02da0a5e20699c7e8ffa471a8879bf1168c8ce9c8c6`
  - `manifest.json` `7dd38252b9394ddd8c75ee75e547ab74888a41f8cd188930b1d514c9a506ce5f`

## 边界

- 诊断只在 `UPLOAD_DEEPSEEK_IMAGE` 且异常为 `RuntimeBoundaryError` 时附加；其他命令、payload 校验失败、auth/PoW/upload 错误不变。
- 不是修复：拿到原因码后才决定针对性修复（如 `ctx_lifecycle_prerender` 需等待文档激活而非放行）。
- 部署前需用户授权；部署后复现步骤：重载扩展 → 在**未刷新的**旧 DeepSeek 页面跑一次 read_image → 读取 `dpp_read_image_diag_v7` 的 `gate_reason` 行或 `dpp_upload_gate_diag_v9`。

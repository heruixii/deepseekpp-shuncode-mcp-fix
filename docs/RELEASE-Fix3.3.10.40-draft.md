# DeepSeek++ ShunCode MCP Fix 3.3.10.40（草稿，未发布）

> 本文是 .37–.40 的合并 Release 说明草稿。**未打 tag、未运行 stage-repo / 发布脚本、未上传 ZIP。** 发布需另行授权，并按项目交接文档 §4 流程执行。

## 版本

manifest `1.14.0.45` / `1.14.0 ShunCode MCP Fix 3.3.10.40`。运行时相对 .36 的改动仅 5+1 个文件：`background.js`、`content-scripts/content.js`、`content-scripts/main-world.js`、`manifest.json`、`_locales/{en,zh_CN}/messages.json`；`fix3-policy.js` 与权限不变。

| 文件 | SHA-256 |
|---|---|
| background.js | `76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5` |
| content-scripts/content.js | `ddda4a9ea97a4105454ab0cea3970eb35212da3c9527a4e82519937e0f4d43fe` |
| content-scripts/main-world.js | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |
| fix3-policy.js（不变） | `c8e843c8bb49e312596dc02da0a5e20699c7e8ffa471a8879bf1168c8ce9c8c6` |

## 修复

- **.38 视觉上传授权误拒（主修复）**：.36 起 `UPLOAD_DEEPSEEK_IMAGE` 在同文档切换过会话的页面内必被 `runtime_message_unauthorized` 拒绝。根因：`DPP_REQUIRE_UPLOAD_CONTEXT_V7` 要求 `sender.url` 的会话段等于 `tab.url` 的会话段，而 `sender.url` 冻结于文档提交时刻。现改为：会话身份仅取自浏览器 tab URL（监听时 `sender.tab.url`、`tabs.get` 三次），并锁定监听时会话；扩展 ID、origin、顶层 frame、active 生命周期、documentId、tab id、DeepSeek 源、上传期间会话不变等检查全部保留，payload 仍不参与信任。
- **.40 技能弹窗启动竞态**：`main-world.js` 在 `<body>` 尚不存在时 `MutationObserver.observe(document.body)` 抛错；现延后至 `DOMContentLoaded`。

## 诊断（固定枚举 / 布尔 / 计数，不含 URL、token、documentId）

- **.37** `chrome.storage.local.dpp_upload_gate_diag_v9` + 页面 `dpp_read_image_diag_v7` 的 `gate_reason` 行：上传门每次拒绝的原因码与探针。
- **.39** 页面 `localStorage.dpp_mw_bridge_diag_v10`：MAIN-world 直写（不经 main↔content 桥），记录 boot / sync_state / bridge_open|close / navigate / fetch_route / send_hook / augment / post_drop 等。

## 验证

- 离线：`tools/validate-fix331040.py` 22 checks / 67 test processes（含 55 个历史套件、视觉 v8、读图 v7/boundary、上传门 v10、桥诊断 v10、弹窗 observe 4 组）全通过；builder 由 .36 基线 hash 锁链式重建，选择性 diff 证明门禁函数除 REQUIRE 外与 .36 逐字节一致。
- 浏览器（2026-09-17）：15:22、15:27、15:43 三次 `capture→upload_ok→request_refs=1→request_ack=1`，模型给出真实视觉回答；新对话首条消息工具注入正常（`tools=24`）。

## 已知 / 非扩展问题

- DeepSeek 服务端偶发 `generation_err`（页面显示“服务器不可用”），扩展会 compact 重试；与本修复无关。
- `read_image` 传绝对路径会被 MCP 工作区策略拒绝（`PATH_OUTSIDE_WORKSPACE`），须先复制进工作区。

## 构建

```
python tools/apply-fix331040.py --build <干净 .36 树> <新目录>
python tools/validate-fix331040.py --root <候选> --baseline <干净 .36 树> --tools tools --output <新目录>
```

# DeepSeek++ Fix 3.3.10.38：上传门禁会话身份改以浏览器 tab URL 为准

状态：候选已构建并通过离线验收（`D:/tmp/deepseekpp-fix331038-20260917/candidate2`，`validation2/report.json`：20 checks / 64 test processes 全通过）。**尚未部署到 live、未发布 Release。**

## 1. 修什么

`.36`/`.37` 的 `DPP_REQUIRE_UPLOAD_CONTEXT_V7` 要求 `vN(context.senderUrl) === context.chatSessionId`。
`.37` 现场诊断（blocker 文档第 9 节）证实这正是浏览器里 `runtime_message_unauthorized` 的唯一命中条件（`ctx_sender_tab_session_mismatch`，其余探针全部正常）。

原因：`chrome.runtime.onMessage` 的 `sender.url` 是 content script 文档**提交时**的 URL；DeepSeek 用 History API 在同一文档内切换会话后它不更新，而 `sender.tab.url` / `chrome.tabs.get().url` 是当前值。任何一次同文档会话切换之后，本文档内所有上传都会被拒，直到 F5。

## 2. 改动（仅一处门禁函数）

`DPP_REQUIRE_UPLOAD_CONTEXT_V7`：

- 删除：`vN(context.senderUrl) !== context.chatSessionId`
- 新增：`context.senderUrl` 与 `context.tabUrl` 必须为非空字符串（原本隐含，现显式）
- 新增：监听器首次看到的 tab 会话 id 记录在 `context.dppListenerChatSessionId`；之后 `TN`（tabs.get）或 `ASSERT_CURRENT` 若得到不同的会话 id，抛 `Image upload conversation changed.`

会话身份来源变为：`sender.tab.url`（浏览器提供）→ `chrome.tabs.get` in `TN` → `ASSERT_CURRENT` 上传前 → 上传后。四次读取必须一致。

保留不变（validate 逐字节锁定）：`wN` / `TN` / `EN` / `DN` / `aI` / `ASSERT_CURRENT` / `DISPATCH`、命令白名单、`fix3-policy.js`、manifest 权限。`sender.url` 仍必须存在、与 `sender.origin` 一致、属于 DeepSeek 源、frameId 0、lifecycle active、documentId 非空；payload 仍不参与信任。

## 3. 工具（`tools/`）

| 文件 | 作用 |
|---|---|
| `apply-fix331038.py` | 复用 `apply-fix331037.py` 的变换（hash 锁 `fix331038-source-sha256.json`），再对 REQUIRE 做唯一锚点替换；版本 1.14.0.43 / Fix 3.3.10.38 |
| `dspp-upload-gate-v10-selftest.js` | 10 组：过期 `sender.url` 被接受且只上传一次；外源/iframe/cached/无 documentId/tab 无会话/上传中导航/监听后 tabs.get 已换会话 全部仍拒绝；诊断无泄漏 |
| `validate-fix331038.py` | 离线门禁：新增 `require_drops_stale_sender_url_comparison`、`require_keeps_all_other_conditions`、`require_is_the_only_gate_body_change` |

构建与验收（不改 live）：

```
python tools/apply-fix331038.py --build <.36 树> <新目录>
python tools/validate-fix331038.py --root <候选> --baseline <.36 树> --output <新目录>
```

## 4. 待做

1. 用户授权后按 .37 流程部署到 live（先 hash 预检、备份、原子替换 5 个文件）。
2. 浏览器验收：在**未 F5、已切换过会话**的页面执行 read_image，期望 `upload_ok → refs → ack → 真实视觉回答`；再读 `dpp_read_image_diag_v7` 确认无 `gate_reason`。
3. 通过后更新 blocker 文档结论、README、Release。

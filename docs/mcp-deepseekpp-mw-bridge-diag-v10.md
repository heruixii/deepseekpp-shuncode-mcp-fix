# DeepSeek++ Fix 3.3.10.39：MAIN-world 桥诊断（“新对话首条消息无工具”取证）

状态：1.14.0.44 已于 2026-09-17 15:41 部署到本机 live（备份 `D:/tmp/deepseekpp-fix331039-20260917/live-backup/`）。运行时 = .38（background/content 字节相同）+ 仅诊断的 `content-scripts/main-world.js` 改动。**未发布 Release。**

## 1. 为什么需要

.38 验收通过后，用户复现：同页点“新对话”→直接发第一条消息→模型称没有工具；F5 后恢复。扩展侧所有 .37 之前的诊断（preflight/turn/traces/v7）对该会话**零记录**。原因是这些诊断全部经 main→content 桥（`vs().post → m()`）转发，桥失效时 `m()` 静默返回 `false`，诊断本身也发不出去。因此需要一条**不经过桥**、直接写页面 `localStorage` 的 MAIN-world 诊断。

## 2. 改动（仅 `content-scripts/main-world.js`，10 个插桩点 + 1 个 helper）

Key：`localStorage['dpp_mw_bridge_diag_v10']`，环形 64 行，字段只允许固定枚举 / 布尔 / 小整数（helper 内白名单校验，键名 `^[a-z]{1,16}$`，字符串值 `^[A-Za-z_]{1,40}$`），连续相同行合并计数 `n`。

| stage | 位置 | 字段 |
|---|---|---|
| `boot` | helper 求值时 | `session`（路径含 `/chat/s/`）、`body`（document.body 是否存在） |
| `sync_state` | `Sa()` 收到 toolDescriptors | `tools` 数量、`body` |
| `bridge_open` / `bridge_close` | `vs()` 桥建立 / `f()` 关闭 | `bridge` |
| `navigate` | `Ts.onNavigate` | `session` |
| `fetch_route` | fetch 钩子识别到 DeepSeek 路由 | `route`、`body`（body 是否字符串）、`known` |
| `send_hook` | `DPP_PREFLIGHT_331018` 的 `mw_send_hook_seen` | `route`、`session`、`tools`（当时 U.toolDescriptors 数） |
| `augment` | `requestAugmentedBody` 入口 | `active`、`bridge` |
| `post_drop` | `m()` 因桥无效丢弃消息 | `active`、`bridge`、`kind`（消息类型枚举） |
| `lifecycle_error` / `main_crash` | 生命周期失败 / 启动崩溃 | — |

builder 的 `MW_PATCHES` 是唯一锚点替换；selftest 反向套用同一列表后必须与 .36 逐字节相同（证明只插入了诊断调用）。

## 3. 工具

`tools/apply-fix331039.py`（复用 .37/.38 变换，hash 锁 `fix331039-source-sha256.json`）、`tools/dspp-mw-bridge-diag-v10.js`、`tools/dspp-mw-bridge-diag-v10-selftest.js`、`tools/validate-fix331039.py`（21 checks / 66 processes；允许改动集加入 main-world.js）。基线需为干净 .36 树（工作树 README 已改，故用 `D:/tmp/deepseekpp-base36`）。

## 4. 读取

页面侧 LevelDB（`Default/Local Storage/leveldb`）中 `_https://chat.deepseek.com` 的 `dpp_mw_bridge_diag_v10`，或 DevTools → Application → Local Storage。判读：

- 有 `fetch_route(route=completion)` 但无 `send_hook` → 钩子在 `s(a)`/body 类型处放行了（形态问题）；
- 有 `send_hook` 且 `tools=0` → content 从未 SYNC 到该文档，或 `clearState` 后未重新同步；
- `augment(bridge=false)` / `post_drop` → 桥断（重点看其前是否有 `navigate`/`bridge_close`）；
- 完全没有 `fetch_route` → 请求不是从该文档的 window.fetch/XHR 发出（例如 prerender/另一个文档）。

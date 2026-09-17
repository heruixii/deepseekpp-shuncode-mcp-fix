# DeepSeek++ Fix 3.3.10.40：技能弹窗 `observe(null)` 启动竞态修复

状态：1.14.0.45 已于 2026-09-17 15:51 部署到本机 live（备份 `D:/tmp/deepseekpp-fix331040-20260917/live-backup/`）。运行时 = .39 + `content-scripts/main-world.js` 内一处表达式修改。background/content 与 .38 字节相同。**GitHub Release 未发布。**

## 1. 现象

扩展错误面板：`main-world.js:321 Uncaught TypeError: Failed to execute 'observe' on 'MutationObserver': parameter 1 is not of type 'Node'`。

## 2. 原因

`main-world.js` 以 `document_start` 注入；content 的 `SYNC_HOOK_STATE` 到达时先 `Sa({toolDescriptors})` 再 `mo()`→`go()`，`go()` 直接 `Y.observe(document.body,…)`。若此时 `<body>` 尚未解析（.39 诊断 `sync_state body=false` 已多次记录到），`document.body===null` 抛错。工具注入不受影响（已在此之前完成），只影响 `/` 技能弹窗在该文档内的初始化。

## 3. 改动（唯一锚点）

```
Y.observe(document.body,{childList:!0,subtree:!0})
→ document.body?Y.observe(document.body,{childList:!0,subtree:!0})
  :document.addEventListener(`DOMContentLoaded`,()=>{Y&&document.body&&Y.observe(document.body,{childList:!0,subtree:!0}),_o()},{once:!0})
```

body 已存在时行为与 .36 完全一致；不存在时延后到 `DOMContentLoaded` 再 observe 并重新查找输入框。

## 4. 验证

`tools/dspp-skill-popup-observe-selftest.js`（4 组，跑真实 `go()/_o()` 文本）：基线在无 body 时复现该 TypeError；候选无 body 不抛、DOMContentLoaded 后 observe 到 body；有 body 时立即 observe 且不注册监听；`go()` 内仅该表达式不同。`tools/validate-fix331040.py`：22 checks / 67 processes 全通过。浏览器验收：重载 + F5 后错误面板不再新增该错误，`/` 弹窗仍可用。

## 5. 工具

`tools/apply-fix331040.py`（链式复用 .37/.38/.39 变换，hash 锁 `fix331040-source-sha256.json`）、`tools/validate-fix331040.py`。基线须为干净 .36 树（`D:/tmp/deepseekpp-base36`）。

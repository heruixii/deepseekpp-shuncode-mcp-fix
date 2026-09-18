> **历史记录补注（2026-09-18）：** 相关修复与后续整改已整合入 [Fix .48](RELEASE-Fix3.3.10.48.md)。下文“未提交/未发布”等描述为当时状态，原始审计证据与不确定性保留。

# Fix 3.3.10.47（扩展版本 1.14.0.52）

2026-09-18 · 新会话请求前缀、服务端失败恢复与任务卡片显示优化。

**状态：本机已部署，离线验证通过；待重载后浏览器验收。未发布 GitHub。**

## 新日志结论

10:40 两个新会话的首请求和其中一次后续请求均为 HTTP 200 SSE 的 generation_err / INCOMPLETE；工具数为 24、授权与增强均成功。10:41 同长度请求成功并连续执行工具。因此这是服务端生成失败，不是 .46 MCP 缓存回归，也不能据此断言首轮存在确定性的冷启动错误。

## 修复与优化

1. 记忆关闭时不再注入“你具有长期记忆能力”及强制自动记忆保存指令；用户可见任务前缀放在请求最前部，原始完整任务和工具 schema 保留。旧标题不自动修改。
2. 同会话、同父回复的一次性 compact 恢复窗口由 12 秒延长到 10 分钟；修复 fetch EOF 时用 done 布尔值代替请求元数据的问题。无自动网络重放。
3. 恢复模式的 schema 精简仅移除冗长说明，保留属性、引用和约束，不再硬截断属性数/分支数/深度。
4. Agent 遇到明确 generation_err 时显示真实中断并停止无效 nudge，不误报完成、不连续消耗配额；不保证第三方服务不会再次失败。
5. 简洁任务卡片：当前动作、成功/运行中/失败/中断、耗时；真实错误原因直接可见。详情默认收起、最终结果独立；隐藏误导性进度条。
6. 手动请求失败显示可关闭的原因提示，不与 MCP 断连混淆；成功和导航清理，不改动 DeepSeek React 消息节点。

完整取证与实施：docs/mcp-deepseekpp-fix47-first-chat-ui-20260918.md。

## 验证

- 新专项 28/28。
- validator：11 checks / 73 processes / 63 suites，全部通过。
- 独立重建 235 文件一致；源篡改/基线篡改/重复输出三项 fail-closed 通过。
- 部署后 live 63/63。
- background.js、fix3-policy.js 未改；授权边界、runtime allowlist、host permissions 等 manifest 非版本字段保持一致。
- DOM 行为为离线桩测试；浏览器首轮成功率、标题与真实视觉呈现尚待验收。

## 哈希

| 文件 | SHA-256 |
|---|---|
| background.js（= .46） | 22e7687c843bea404d53457cf5a44533dd29e9c062bb33f991b1480e97d9a74d |
| content-scripts/content.js | 2f4a79a13bbcbe6f029a61679a7ca6feeaa49c7a5257d57b12fcfbb53efbf3c2 |
| content-scripts/main-world.js | 50ea860665adf7710e645d9708ac9b08fc59d27059ebae3e78165068677df7fe |
| fix3-policy.js（= .46） | 39915841f22a165e1cc395e17d4fdff5651050c2d70c2e3bc6291ac3b26f38c5 |

## 本机升级与回退

live：D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3。

1. edge://extensions 重新加载 DeepSeek++，确认 1.14.0.52。
2. 关闭旧 DeepSeek 标签，打开新页面和第一个新会话，先执行只读 MCP 任务。
3. 若服务端再次 generation_err，等待 Agent 停止后再发送“继续”，不要在运行中反复发新消息。

回退点：D:/tmp/DeepSeekPP-Fix331046-pre331047-20260918（部署前完整 .46 备份）。

## 构建

```bash
python tools/apply-fix331047.py --build D:/tmp/deepseekpp-base36 <全新候选目录>
python tools/validate-fix331047.py --root <候选目录> --baseline D:/tmp/deepseekpp-base36 --output <全新验证目录>
```

源锁：tools/fix331047-source-sha256.json。新增源：tools/dspp-startup-ui-v47.js、tools/dspp-schema-v47.js、tools/dspp-task-ui-v47.css。机器回执和日志保留在本机 tmp 与私有 local/fix331047/，不放公开 docs。

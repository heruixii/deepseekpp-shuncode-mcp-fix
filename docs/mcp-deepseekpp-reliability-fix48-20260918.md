# .48 实施记录与接手说明

本记录对应用户授权“进行完整修复并更新文档和GitHub”，并选择提交/推送当前 main 分支。

## 问题、修复与证据

| 问题 | 实施 | 验证与边界 |
|---|---|---|
| editMessage 不命中 compact | 从 SSE 保留 request_message_id；解析 message_id / child_message_id，按路由与精确失败分支匹配 | 真实 ja 解析函数和恢复管理器执行测试；没有确切服务端 ID 时不猜测 |
| 重开后恢复状态丢失 | 有界、TTL 的分支提示存入 localStorage | 模拟两个页面 JS 环境读同一存储、消费、失效、错误分支、存储禁用测试；不作为工具授权 |
| read_image 503→相同ID重试→replayed | 仅在 Fu 的初始化阶段尝试一次；工具发送后不重放 | 实际 Fu 与 i2 执行测试：2次初始化、1次工具发送；双503零发送；取消/模糊工具结果不重放 |
| checkpoint 落后与停止状态覆盖 | 工具发送/返回/步骤完成落盘；执行者+修订号+过期拒绝；Web Locks | 两个真实 kU 存储实例并发测试；新旧写顺序、异页面写、累计统计；原那次中断的唯一原因仍未知 |
| NUL 导致 rg 搜索失败 | schema支持时排除 NUL，结果附带范围说明 | 真实 MCP 在原目录只读搜索正常结束、零匹配；不删除特殊文件 |
| 大工具提示、长会话难以恢复 | 超过字符阈值精简描述符，保留 schema；错误提示建议摘要交接新会话 | 不修改用户完整任务、不把累计 tokens 当上下文长度；未声称第三方 generation_err 根除 |

## 文件与职责

- `tools/apply-fix331048.py`：.36→…→.47→.48 链式构建、唯一补丁断言、语法检查、新输出目录保护。
- `tools/fix331048-source-sha256.json`：锁定本版实现/验证器/测试以及 .47 入口和锁文件。
- `tools/dspp-recovery-v48.js`：分支提示存储与编辑/重新生成精确匹配。
- `tools/dspp-mcp-init-v48.js`：初始化阶段受限重试；不调用 tools/call。
- `tools/dspp-runtime-v48.js`：描述符预算、NUL搜索范围、checkpoint计数/身份/并发锁及保存诊断。
- `tools/dspp-reliability-v48-selftest.js`：50项新行为测试，执行打包产物中的实际函数。
- `tools/validate-fix331048.py`：独立重建、完整范围/安全不变量、64套件及外部边界测试。

## 验证回执

- 候选：`D:/tmp/deepseekpp-fix331048-candidate1-20260918`，236文件。
- 验证：`D:/tmp/deepseekpp-fix331048-validation1-20260918/report.json`，12检查/74进程/64套件通过。
- 安全与部署：`D:/tmp/deepseekpp-fix331048-safety-20260918/`，3项fail-closed通过，41个变更文件，部署后64/64。
- 回退：`D:/tmp/DeepSeekPP-Fix331047-pre331048-20260918`，部署前完整 .47，逐文件核验。
- 本机 live：`D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`，文件版本1.14.0.53。本次不强制重载正在运行的浏览器。
- 私有副本：仓库 `local/fix331048/`，已忽略，不上传原始日志、数据库、终端输出或备份。

### 产物 SHA-256

| 文件 | SHA-256 |
|---|---|
| background.js | 397fab1b6ed8d45b6f176bae6cecd9306626ebd591ed54f4da822e0d0f6bda9c |
| content-scripts/content.js | 24a71f3e5e1dc20a77ea40072568dd2fda54d9f76644fdefe88a0963f29635c2 |
| content-scripts/main-world.js | 269541d8045fceb6b68e42141acfabc13cb39c5769b7054a13bebafb91afa6b7 |
| fix3-policy.js（不变） | 39915841f22a165e1cc395e17d4fdff5651050c2d70c2e3bc6291ac3b26f38c5 |

## 诊断使用及剩余边界

`dpp_trace_write_diag_331048` 保留最近64次保存事件：requested、confirmed、stale_rejected、failed。记录时间、trace/loop/writer、修订号、状态、停止原因、步骤/工具/待确认数量及错误类型，不存提示、工具输出或原始异常消息。requested 后没有 confirmed 不能算已成功保存。

Web Locks 只在API可用时提供同源标签串行化；不可用时不夸大保证。关页保存仍受浏览器销毁时序影响，所以结果在关页前的每次执行返回时即保存，而不是只依赖 pagehide。外部命令在关页后可能继续执行，恢复摘要中的未确认ID必须先核查，不能自动重放。

原始 .47 trace 已轮转，不改写其历史记录、不补造“成功执行”。新实现不自动接管旧页面尚在执行的 Agent，用户应待任务停止、重载扩展后再开始验收。发布说明列出的行为与离线/现场只读验证严格区分；真实浏览器/DeepSeek生成流程仍待升级后验证。

安装和回退见 [Release .48](RELEASE-Fix3.3.10.48.md)。先前审计见 [新日志审计](mcp-deepseekpp-fix47-newlogs-audit-20260918.md)。

## Git 归档字节一致性

发布前发现原 Git 文本自动换行会改变部分已锁定 .45 测试/构建文件和导入资产的 CRLF 字节。.48 用精确字节保留属性修复：源锁文件、构建源、测试及相关导入资产在 Git index/归档中与已验证文件一致；真实行尾空格仍检查，CRLF本身不再误报空格。不改写哈希以迎合损坏归档。公开包从 main 的 Git 归档生成，包含运行时、工具与更新文档；不包含 .git 或 local 私有证据。

# 本轮 SVG 读图阻塞：日志核查

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

核查日期：2026-09-17。结论：本轮视觉链路确实失败，但不能归因于“ShunCode 始终剥离图片”。本次只取证、复核与更新文档，未修改运行代码、重启程序或发布新版。

## 1. 本轮实际行为

记录显示22步、30次工具调用，最终状态为 `complete`；模型文本承认无法取得视觉依据、没有交付。这不是上一轮“读图后长 patch 被误当完成”的相同现场：本轮有多步排查，但阻塞结论仍被归类为完成。

原提示末尾明确要求使用 read_image，因此本轮不能作为“不额外提醒也主动看图”的独立验收。

直接 read_image 执行共13次：4次 FILE_NOT_FOUND、6次 network error、3次工具成功。模型所说“多次调用全部是工具 success”与实际记录不符。通用诊断 tool_failed_or_truncated 不能单独证明字节被截断；本轮多处对应的是文件不存在或网络调用失败。

## 2. 确定的上传拒绝

以下时间使用 UTC+8：

| 时间 | 图片字节数 | 结果 |
|---|---:|---|
| 12:40:28.893 → 12:40:28.900 | 18,731 | upload_start 后7ms返回 runtime_message_unauthorized |
| 12:40:37.190 → 12:40:37.199 | 18,731 | upload_start 后9ms返回同一错误 |
| 12:41:15.741 → 12:41:15.743 | 2,168 | upload_start 后2ms返回同一错误 |

三次均先出现 capture；随后 request_refs 为0，没有本轮 upload_ok/request_ack 成功证据。扩展已取得图片字节，失败位于随后上传的扩展后台运行时授权边界。2,168字节也失败，不应把此拒绝归因于图片太大，更不应继续盲目缩图。

`[image bytes omitted]` 的替换逻辑存在于扩展 content.js 的结果清理函数中，用于避免把 base64 当正文送给模型。该标记不等于 ShunCode 未返回图片，也不等于图片已作为视觉附件成功进入模型。

## 3. ShunCode 原生复核

通过当前 MCP 会话只读调用工作区 `_refimg/probe64.jpg`，返回 content 类型为 text + image，原生 image 的 base64 长度为2,892字符。说明当前 ShunCode 至少能返回该小图的原生图像块；此复核不经过 DeepSeekPP 的 Web 上传，因此不能证明 Web 链路已恢复，也不证明全部格式/尺寸正常。

## 4. 已知与未知

- Edge 登记的扩展目录与本机部署目录一致。磁盘 manifest 为1.14.0.41。
- content SHA-256：e66f24d5b0be89089354c39cbdf5807b2180cad1711b53fce5c1d8346c40f1ec。
- background SHA-256：4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc，与已发布代码一致。
- 磁盘一致不能证明浏览器当前驻留的 service worker/content script 版本。
- 后台上传门要求同扩展、DeepSeek 顶层活动文档、documentId、有效会话及当前标签页会话一致。现有返回统一为 runtime_message_unauthorized，未保留具体失败子条件，因此尚不能断言是哪项拒绝，也不能断言一定是旧后台、SPA切换或 ShunCode 授权。
- 前次成功上传和离线回归不能替代本轮失败现场；目前应记录为“磁盘部署及发布完成，浏览器视觉验收失败，原因待进一步细分”。

## 5. 后续修复重点

1. 在不记录 token、原图、完整 URL 或原始 sender 对象的前提下，为后台授权拒绝补充固定原因码，以及实际加载版本诊断。
2. 针对实际命中的条件修复；保留扩展身份、来源、顶层 frame、活动文档及会话隔离，不以删除授权检查解决问题。
3. 区分工具成功与视觉附件上传/引用成功，避免只凭 read_image 的 ok 满足视觉完成判断。
4. 让“环境阻塞、未交付”与普通 complete 状态区分，并对已确定的非重试性授权失败停止无效缩图/重复尝试。
5. 修复后再验证：capture → upload_ok → refs → ack → 实际视觉回答/产物。没有做到，不宣布修好。

本次未修改扩展或 ShunCode 运行代码，未重新发布 GitHub；私人日志快照只保留在本机维护目录，不上传公开仓库。


---

# 下一智能体接手说明：DeepSeekPP 视觉上传阻塞

更新：2026-09-17。用户最新要求：先更新文档，额度将尽，把工作交给下一智能体。本轮只交接，不继续修代码、不发布。

## 一、必须先读的当前入口

远程 Windows 工作区：`D:/tmp/gh-deepseekpp`（DSPP 独立项目目录，2026-09-17 起与 Athena 计划分离）。

1. `docs/mcp-deepseekpp-visual-blocker-20260917.md`：最新现场失败证据及本接手说明，优先级最高。
2. `docs/mcp-deepseekpp-visual-workflow-v8.md`：.36实现、限制、离线测试、部署及发布记录；其中“待现场复测”已被本轮失败证据覆盖。
3. `DeepSeekPP-Fix3-项目交接文档.md`（仓库根目录）：头部有本轮失败提示，旧版本段落只按历史阅读。

黑曜石库：`C:/Users/29066/Documents/GitHub/ALTRKIE-`。当前入口是 `dspp/00-总览.md`、`01-当前使用与恢复.md`、`02-维护交接.md`、`03-视觉与作画规则.md`。前三篇已标注本轮失败；03硬规则不改。不要再迁移目录，不要重新建立另一套“最新文档”。

## 二、发布和磁盘状态——不要重做已完成工作

- 已正式发布 Latest：`v1.14.0-fix3.3.10.36`，扩展版本 `1.14.0.41`。
- Release：https://github.com/heruixii/deepseekpp-shuncode-mcp-fix/releases/tag/v1.14.0-fix3.3.10.36
- 代码提交：`16a9219ff8dbd3601fedecfb459d1d5431e04248`。
- Git tree：`aed802b878454b77bb6d82cf463fb21bcd133e1f`。
- Repo：`D:/tmp/gh-deepseekpp`，发布后检查为clean；本轮未修改公开repo。下一次操作仍须重新检查状态，不能假定一直clean。
- live：`D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`。
- Edge扩展ID：`kdmpkkahkhdmdhfkdihkopikgcocbpbf`。登记目录与live一致。
- content SHA-256：`e66f24d5b0be89089354c39cbdf5807b2180cad1711b53fce5c1d8346c40f1ec`。
- policy SHA-256：`c8e843c8bb49e312596dc02da0a5e20699c7e8ffa471a8879bf1168c8ce9c8c6`。
- background SHA-256：`4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc`，.36未修改该文件。
- 发布ZIP SHA-256：`4ff3027c0112a3593fd53c47fa62f28f80c7d4e1cdc69eddc453abfd9b18c89b`，109文件；ZIP、验证JSON、SHA256SUMS三个附件下载及API digest核验通过。
- .36通过14工程检查、65测试进程，含48视觉/22读图/16后台/22维护/55旧套件及6语法检查；这不是模型端到端成功证明。
- 磁盘代码已确认，但浏览器驻留service worker/content script实际版本未确认。不要把当前失败直接归因于用户没重载。

构建维护目录：`D:/tmp/deepseekpp-fix331036-20260917`。
- 最终构建与完整报告：`candidate3/`、`validation3/`；candidate/candidate2是历史。
- 发布前Git树验证：`git-candidate/`、`git-validation/`；安装包：`artifacts/`，解压复测：`zip-extracted/`。
- 原始部署备份：`live-backup/`；最终部署回执：`live-deployment.json`；初次候选content另存，不覆盖备份。
- 笔记原始迁移回执：`obsidian-backup/receipt.json`；发布后笔记更新备份：`post-publish-notes-backup/`。不要改写初始迁移证据。
- 已执行过stage-repo、迁移、push/release脚本，不能重跑。新版本应使用独立候选/报告目录，禁止重标.36 tag或覆盖已核验附件。

## 三、最新现场证据：要读这些，不要再引用旧成功日志代替

私有快照：`D:/tmp/svg-vision-recheck-20260917-124245/`。
- `vision-diag.json`：扩展读图捕获/上传/引用阶段记录，包含早期历史，须按时间筛选本轮。
- `selected-extension.json`：只选取的工具历史、agent trace和轮次诊断。
- `web/`、`extension/`：复制得到的LevelDB只读快照。它们可能含敏感数据，禁止上传公开仓库。
- `handover-backup/receipt.json`：上一轮更新10份交接/笔记头部的前后哈希及备份。

本轮 loop：`c9db6336-4db9-4196-a709-133c10e97ec2`。
本轮会话：`5b81964d-bec1-4c90-a009-6ab0f46bc292`。
开始时间戳：`1789619863069`；结束：`1789620110332`。
trace数组：`dpp_inline_agent_traces`，本快照1项；其 `steps[].toolExecutions[]` 保存清理后的结果。原始工具历史 `deepseek_pp_tool_history` 中近期read_image仍可见data URI；只输出存在性/长度，不打印base64。

确定事实：
- 22步、30工具，直接read_image 13次：4次FILE_NOT_FOUND、6次network error、3次工具success。
- 三次success先capture，再upload_start，分别18,731B、18,731B、2,168B，随后7ms/9ms/2ms内收到 `runtime_message_unauthorized`。
- 对应时间（UTC+8）：12:40:28.893、12:40:37.190、12:41:15.741。
- 后续refs=0；本轮无upload_ok/ack成功证据。不能说只是模型拒绝，链路确实失败。
- 原生复核当前MCP `_refimg/probe64.jpg` 返回text+image，image base64长度2,892字符。该复核不经Web上传，不能当作Web修复验收。
- `[image bytes omitted]` 替换发生在content.js结果清理中；不能据此指控ShunCode始终剥离图片。
- 最终模型文字承认受阻未交付，trace却为complete，最后decision为task_complete。
- 原提示末尾明确写了使用read_image，因此本轮不能证明无需额外提醒也自动选工具。
- 真实工作区临时图目录是 `D:/tmp/gh-deepseekpp/local/_refimg/`；用户粘贴的模型摘要省略了分隔符。不要删除或覆盖该目录及源图。

旧成功快照 `D:/tmp/svg-vision-investigate-20260917-115634/` 仅用于对照，不是本轮成功证据。

## 四、下一步定位顺序（尚未执行）

### A. 优先定位上传授权拒绝，不要盲改ShunCode

真实后台函数：
- `wN(sender, policy)`：运行时sender正规化。
- `TN(context, tab, policy)`：tabs.get后的顶层来源及会话正规化。
- `EN(message, context)`：命令白名单及上传专项门禁。
- `DPP_REQUIRE_UPLOAD_CONTEXT_V7(context)`：deepseek_content要求frameId=0、documentLifecycle=active、documentId非空、chatSessionId非空、senderUrl解析会话与context会话相同。
- `DPP_ASSERT_CURRENT_UPLOAD_V7(context)`：经 `aI` → tabs.get → TN 校验当前标签页，会话不能变化。
- `DPP_DISPATCH_UPLOAD_V7`：上传前后校验、错误归类。
- `DN` 和上传catch把多种拒绝压成同一runtime_message_unauthorized；现有日志不足以知道命中的具体条件。

先获取实际加载版本及固定拒绝原因码。如需新增诊断，必须read-before-edit、哈希预检、备份、小范围修改并同步文档。诊断只记录固定枚举/布尔值和必要阶段，不记录token、原图、完整URL、原始sender对象、认证headers。不要以payload自报会话/身份为可信证据。

可能需要区分：旧驻留代码、缺失或非active生命周期、documentId缺失、sender URL与当前tab会话不一致、上传期间真实导航等。以上都是待验证假设，不是已经证明的根因。不得直接删授权检查、扩大任意来源/iframe权限或强制恢复用户取消。

### B. 分开检查其他问题

- 6次network error需单独关联MCP响应/传输，不能用tool_failed_or_truncated这个泛化标签认定“大图被截断”。
- .36结束前检查只证明成功read_image调用，不证明上传/refs/ack。需研究如何把传输结果与本轮视觉证据关联，并允许明确报告阻塞而不是强制无限读图。
- task_complete遇到受阻未交付时，需核实状态契约；不能仅凭某个词的正则把所有合理说明改成失败，也不能把受阻当成功产出。
- 对确定非重试性的上传授权拒绝，应避免反复缩图/重复相同请求；保留用户明确重试以及授权恢复后的新尝试。

### C. 测试与验收

- 覆盖真实sender正规化→授权门→dispatch路径，不只mock上传成功。
- 加入会话导航、同文档URL变化、跨会话/跨来源/iframe、非active/缺documentId、失效tab及上传中导航等正反例；先明确安全预期，再调整实现。
- 保持.36视觉48组、读图22组、后台16组、原生维护22项、旧55套件不回归。若要修改后台，.36 validator“background不变/恰好5文件变化”不可直接作为新版本验收规则；建立新版本基线和允许变更清单，不篡改旧hash锁。
- 最终必须浏览器现场验证capture→upload_ok→refs→ack→真实看图回答/产物。验证主动选工具时用不额外写read_image的提示；验证画面质量需实际渲染/看图，不能靠语法测试。
- 用户自行重载或明确授权后再进行所需操作；不要擅自重启ShunCode/浏览器、改浏览器设置、用户数据库或其他项目。

## 五、文档与发布纪律

- 用户要求每次改动更新文档；当前重点先修复与验收，不要仅把状态文案改成成功。
- 黑曜石当前目录已整理：4当前入口+21历史原稿+1历史索引。原始迁移修复53链接、校验131链接；后续仅dspp内部复核126条，与包含外部总索引的原统计口径不同，不是丢了5个链接。
- 保留禁止伪作画规则：不reveal/copy+mask冒充绘画；不将trace/convert隐瞒成视觉重绘；本SVG任务禁止嵌原图、Base64图片、外图及Canvas。
- 本轮未修新代码、未发布新版本。后续真正修复且验证后再按用户授权推进GitHub；私人vault、图片、原始trace/LevelDB、备份及凭据都不得发布。

## 六、工具与读取注意

Arena共享工作区 `/home/user` 有 `mcp.sh`、`rpy.sh`（run_command 传脚本）与 `tools.json` 可继续调用已有远程MCP。连接参数仅使用本地封装，不抄入公开文档；失联时确认连接，不凭空声称修改成功。

远程是Windows的PortableGit Bash。run_command的外层工具成功不代表内层脚本成功，必须看内层status、exit_code和输出。Python文件操作显式UTF-8，默认GBK可能解码失败；Git/gh设置PAGER=cat。大base64/长minified文本会被PTY折行重叠污染，优先远端原字节操作，必要传输用每行60字符的小块。LevelDB只复制快照后解析，不改浏览器库、不解锁或杀进程。

本地本轮取证回执：`svg-recheck-snapshot.json`、`svg-recheck-context.json`、`svg-recheck-boundary.json`、`svg-recheck-summary.json`、`svg-recheck-final-evidence.json`、`svg-recheck-native-summary.json`、`svg-recheck-docs-final.json`。部分历史输出含私有内容，不公开。`svg-recheck-summary.json`末尾因默认GBK读取Preferences失败，前面取证已输出；后续final-evidence已用UTF-8完成相关复核。

## 7. 2026-09-17 下午补充：授权链核对与会话对照（未改代码）

- live `background.js`（SHA `4f89a4d8…e3abc`）中 `runtime_message_unauthorized` 唯一来源为 `bN.unauthorizedSender`，抛出点：`wN`（非本扩展 / lifecycle≠active / senderUrl 缺失或无效 / origin≠URL / 非 DeepSeek 顶层 frame / tab URL 非 DeepSeek / 无顶层 frame 证据）、`EN`（命令白名单；`UPLOAD_DEEPSEEK_IMAGE` 已在 xN 中，v7_bak 中没有）、`DPP_REQUIRE_UPLOAD_CONTEXT_V7`（frameId≠0 / lifecycle≠active / documentId 空 / chatSessionId 空 / `vN(senderUrl)!==chatSessionId`）、`aI`→`TN`（tab 不可用 / tab id 不一致 / tab URL 非 DeepSeek）、`ASSERT_CURRENT`（上传前后会话变化）。
- `chatSessionId` 在 `wN` 中取自 `vN(tab.url ?? sender.url)`，而 `REQUIRE_UPLOAD_CONTEXT_V7` 要求其等于 `vN(sender.url)`；两者不一致时同步抛出，对应毫秒级拒绝。
- 会话对照：11:53:25 成功上传发生在会话 `dc7f7509…`（08:24 起即存在，页面以该 URL 直接加载）；12:40 三次失败均在会话 `5b81964d…`，其首条 completion 即本轮开始 12:37:43——即本轮从“新对话”经 SPA pushState 进入 `/a/chat/s/5b81…`。两次使用同一 background.js（mtime 11:09:53）。
- 因此最强假设为：新对话 SPA 切换后 `sender.url` 与 `tab.url` 会话段不一致（或 `documentId` 为空）。**尚未证实**，不能排除驻留旧 content script。零代码验证方法：重载扩展后分别在（a）直接加载旧会话 URL、（b）新对话→首条消息 两种场景各跑一次 read_image，对照 `dpp_read_image_diag_v7`。
- 2026-09-17 下午已将 DSPP 全部文档/脚本/私有取证从 `D:/learn/Athena计划` 迁至 `D:/tmp/gh-deepseekpp`（docs/ tools/ local/），迁移回执 `D:/tmp/dspp-migrate-20260917/receipt.json`（含原文件备份与哈希）。

## 8. 2026-09-17 14:26–14:35 用户现场三场景验证（零代码，扩展已重载为 1.14.0.41）

数据源：快照 `D:/tmp/svg-vision-verify-20260917-143703/`（web localStorage `dpp_read_image_diag_v7`，需 snappy 解块；extension `dpp_inline_agent_traces`/`dpp_web_response_diag_331015`）。私有，不发布。

| 场景 | 会话 | 时间 | 结果 |
|---|---|---|---|
| A 地址栏直接加载旧会话 URL | `dc7f7509…` | 14:26:25 / 14:26:52 / 14:27:05 / 14:27:35 | capture→upload_start(2,168 / 2,168 / 18,731 / 36,076 B)→**runtime_message_unauthorized**（1–19 ms），refs=0 |
| B 新对话（SPA 切换） | `f41cba92…` | 14:28:55 / 14:29:29 / 14:29:38 | 同上，三次全部被拒 |
| C 同一会话 F5 刷新后 | `f41cba92…` | 14:33:53 | capture→upload_start(2,168 B)→**upload_ok**(14:33:57)→request_refs=1→request_ack=1；模型给出真实画面描述 |

结论：
- **第 7 节“新对话 SPA 切换导致会话不一致”的假设被推翻**：A 是直接加载的旧会话，同样失败；且 11:53 同一会话、同一 background 曾成功。
- 失败与图片大小、会话新旧无关，与**文档实例**相关：A 与 B 处于同一 document（B 由 A 的页面 SPA 新建），全部失败；F5 产生的新 document 全部成功；上午成功的也是另一 document。即某个在 document 生命周期内固定的 sender/tab 属性不满足授权门，重新加载文档后恢复。
- 待区分的候选（均在门内、均是同一错误码）：`sender.documentLifecycle` 非 `active`（如地址栏预渲染后激活的文档）、`sender.documentId` 缺失、`sender.url` 与 `tab.url` 会话段不一致、`tabs.get` 返回的 `url` 缺失。仅凭现有日志无法再细分——后台把所有拒绝压成同一码，这正是第 5 节第 1 条要补的固定原因码。
- 步骤 2 的“可绕过”结论：用户侧临时规避 = 任务开始前 **F5 刷新 DeepSeek 页面**；这不是修复。
- 另：C 之后 14:34:59 的追问轮以 `unregistered_tool_continue_331036`×3 → `unexecuted_work_limit_331036` 结束为 error，属 .36 长块门在无工具追问时的误触发，需单独记录，不与上传阻塞混淆。

下一步（待用户授权）：制作 .37 候选，仅在后台授权门增加固定原因枚举（`gate_stage` + 布尔位：hasTab/frameId0/lifecycleActive/hasDocumentId/senderSession/tabSession/sessionsEqual/tabsGetOk），写入 `chrome.storage.local` 有界环形数组并随响应返回 `reason`；不记录 URL/token/sender 原文，不放宽任何检查；配套 16 组后台边界测试扩展与新的版本基线。

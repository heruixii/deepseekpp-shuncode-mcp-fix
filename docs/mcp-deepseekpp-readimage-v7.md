# DeepSeekPP read_image v7：上传权限接线与真实分发链验证

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 本轮浏览器验收失败（优先于下方此前待验状态）**：磁盘仍为.36/1.14.0.41，GitHub发布不变；本轮22步/30工具，3次取得图像字节后上传被 runtime_message_unauthorized 拒绝，refs=0，2,168字节也失败。其余直接读图含4次文件不存在、6次网络错误，并非全部success。当前MCP小图复核返回原生image块，不能归因于ShunCode始终剥离。具体后台拒绝子条件及浏览器驻留版本未取证；阻塞仍被记为complete待修。本次仅核查，未改运行代码或发布新版。 详见 docs/mcp-deepseekpp-visual-blocker-20260917.md。
> 部署状态（脚本维护）：v8/.36正式磁盘已更新为1.14.0.41；content e66f24d5…f1ec，policy c8e843c8…c8c6，background不变。浏览器重载/新模型验收待进行，分发回执见v8文档；2026-09-17。

> **2026-09-17 v8 当前接手入口**：Fix3.3.10.36 / 1.14.0.41 已部署本机磁盘，修复视觉主动工作流与长未注册工具块误完成；48视觉/22读图/16后台/22原生维护/55旧回归、14工程/6语法通过，正式文件复测48/22/16通过。浏览器尚需用户重载，新模型SVG端到端未验证；GitHub已正式发布 Latest v1.14.0-fix3.3.10.36，提交16a9219ff8dbd3601fedecfb459d1d5431e04248；三个远端附件下载SHA-256及API digest一致。黑曜石已将奇思妙想整理为dspp：4当前入口+21历史原稿+1历史索引，53处链接修复、131处校验，原始备份保留，未推送私人笔记库。详见 docs/mcp-deepseekpp-visual-workflow-v8.md。下方旧版状态按历史阅读。

## 当前状态（2026-09-17）

- 用户已授权修复 v6 浏览器实测上传失败，并要求每批更改更新文档。
- 本轮实现、双文件部署及小 JPEG 的真实 HTTP 上传/引用/响应链路已核实；模型回答与缩略图主要构图相符，但有历史上下文，不能当严格盲测。
- **不得把离线测试等同于实际 HTTP 上传或模型识图成功。** 用户本次已授权核实后 GitHub 发布；不自动重启程序、不更改侧栏设置、不发布用户原图/原始日志/凭据或完整 ShunCode 安装。
- 基础发行版仍为 manifest `1.14.0.39 / Fix 3.3.10.34`，v7 是本地功能补丁。

## 1. 已确认的两个阻断点

### 1.1 运行时权限门（确定）

故障记录见 `docs/mcp-deepseekpp-readimage-upload-boundary.md`。现场成功捕获3043 B图片，`upload_start → upload_failed` 仅2ms；真实 `EN/xN/DN` 复跑确认：DeepSeek 内容脚本无权调用 `UPLOAD_DEEPSEEK_IMAGE`，处理器未进入。v6 自测模拟了上传回调，漏掉真实发送方权限门。

### 1.2 错误依赖侧栏聊天开关（本轮新确认）

- 故障快照 `D:/tmp/readimage-v6-upload-20260917-105431/extension` 不含 `deepseek_pp_chat_enabled`。
- 当前后台 `iw()` 仅在该键严格为 true 时返回 true，缺省为 false。
- 原 `zF.re` 上传服务先检查这个开关；即使放开消息权限，仍会返回 `chat_disabled`。
- 快照中的缓存鉴权头存在，仅核对 Authorization 是否存在，未读取/打印凭据正文。它不证明 token 当前有效。

修复必须同时接通消息权限与主页面上传服务，不能擅自把侧栏聊天开关改为 true，也不能全局删除开关。

## 2. 安全与行为不变量

1. `xN` 仅新增 `UPLOAD_DEEPSEEK_IMAGE` 一条命令，其他命令权限不变。
2. 保留现有 `CN/wN/EN`：同扩展 runtime ID、非 native sender、DeepSeek 来源、顶层 frame 与 active 文档检查。
3. 新上传路径进一步要求归一化 context.frameId=0、documentLifecycle=active、非空 documentId、有效 conversation ID，发送文档 URL 的会话必须与 context 一致。
4. 命令进入 `RN/LN → aI/TN` 的浏览器当前 tab 校验；上传服务在鉴权、PoW、上传前以及返回 ID 前再次校验相同会话。
5. 主页面“content=true”标记与校验回调只能由可信后台 handler 根据已验证 sender 创建。payload 经既有 `xP` 解码，不接受用户传入信任标记/回调。
6. 侧栏/扩展页面继续走原 `service.uploadImage(payload, tabId)`，保持原 chat_enabled 控制与错误返回。不写入或开启任何设置。
7. 保留 `bP` 的8MiB、MIME、data URL、base64长度与实际 sizeBytes 一致性校验；复用原鉴权/PoW/文件处理服务，不引入新端点。
8. 主页面图片引用依然按运行隔离、成功响应后消费；API 通道、完成门、MCP能力句柄、DOM保险丝等保持不变。
9. 取消/超时不能保证撤销后台已发出的 HTTP 上传；迟到结果不得进入新运行。会话在上传中改变时拒绝返回 file ID，但不能撤销已经完成的服务器上传。
10. 当前 tab URL/session 再校验不能证明“相同URL重载后的新 documentId”；不新增 webNavigation 权限，不声称实现了后台实时 documentId 撤销。浏览器提供的初始 documentId/lifecycle 检查保留。

## 3. 代码接线

### background.js

- `xN` 增加单个命令；`LN` 增加该命令以启用浏览器 tab 再校验。
- `EN` 在已有检查之后调用 `DPP_REQUIRE_UPLOAD_CONTEXT_V7`。
- 上传 typed handler 由直调服务变为 `DPP_DISPATCH_UPLOAD_V7(service, decodedPayload, normalizedContext)`。
- 主页面分支创建内部可信对象，带 `content:true`、phase与 `assertCurrent`；扩展页面不获得该对象。
- `zF.ie/re` 仅传递内部对象；仅当对象来自主页面分发器时，主页面上传不依赖侧栏开关。侧栏原分支完全保留。
- 上传失败返回固定 code，不向内容脚本暴露网络响应原文、凭据或本地文件路径。

可读源：`tools/dspp-readimage-v7-background.js`。它被 builder 嵌入真实 `background.js`，不是另一个常驻后台。

### content-scripts/content.js

- v6 helper 替换为 `DPP_CREATE_READIMAGE_V7`，保留 Jz 的既有生命周期接线；局部变量名 `DPPVisionV6` 仅为减少无关改动保留，不表示仍运行旧 helper。
- 诊断键升级为 `dpp_read_image_diag_v7`，保留最多64条有界元数据。
- 失败枚举：`runtime_message_unauthorized`、`runtime_message_invalid`、`runtime_unavailable`、`chat_disabled`、`upload_busy`、`auth_missing`、`auth_rejected`、`auth_failed`、`pow_failed`、`invalid_image`、`upload_timeout`、`upload_aborted`、`invalid_upload_response`、`upload_failed`。
- 只记录固定枚举、时间、计数、字节数，不记录 raw error/payload/文件ID/Authorization/PoW/header。

可读源：`tools/dspp-readimage-v7-runtime.js`。

## 4. 基线、候选和回退

完整修改前扩展快照：`D:/tmp/DeepSeekPP-readimage-v7-20260917/frozen-v6/`。

| 文件 | v6 基线 SHA-256 | v7 候选 SHA-256 |
|---|---|---|
| content-scripts/content.js | `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9` | `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4` |
| background.js | `ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32` | `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc` |

初始候选大小：content=902208 B，background=654147 B，二者 Node 语法检查通过。manifest 精确锁定 SHA `b86a6f88793f96de6104bd0a8b2f64de97aef8e3c2722172e75ea9080fe4498f`，不增权限、不改版本字段。

补丁器：`tools/dspp-readimage-v7-patch.py`。

- 默认只读，锁定两份输入、manifest、helper源与两份输出哈希；拒绝未知/混合版本对。
- `--build` 仅写新的隔离完整目录，禁止正式目录及其子目录。
- `--apply` 预检并暂存所有文件，保存两份 `.v7_bak`（修改前v6），同步文档后安装两份运行文件；失败尝试回滚。
- 并非跨文件系统/断电原子事务。正式目录两文件替换期间应避免用户主动重载；未知半升级不得强行覆盖。
- `--rollback` 必须当前两份都是精确v7且备份两份都是精确v6，回退两个文件和文档当前状态。v6 是已知上传失败版本，并非最终可用状态。
- v6旧补丁器因background哈希不再匹配会拒绝操作；v7之后不要使用旧脚本回滚。

## 5. 验证计划与门槛

### 必须执行的离线测试

1. `tools/dspp-readimage-v7-selftest.js`：v6的20组helper行为与候选真实Jz集成，预期22组；新错误分类不得破坏回退、隔离、去重、超时和隐私。
2. `tools/dspp-readimage-v7-boundary-selftest.js`：抽取**真实 listener、sender gate、xP/bP、typed handler、zF上传服务**执行。只模拟浏览器tabs API、鉴权/PoW/文件网络依赖；没有执行完整扩展启动或真实HTTP请求。
3. 真实边界测试至少包括：v6原失败复现、新白名单仅多1条、主页面/侧栏开关隔离、伪造payload无法提权、错来源/iframe/错runtimeID/native/inactive/缺document拒绝、当前tab变更/消失、auth后与PoW后导航拒绝、上传后不返回跨会话ID、真实payload校验、错误枚举保密、完整capture→listener/service→ref链。
4. 按本计划运行扩展原有55个selftest，不运行Athena/VN全量测试或真实模型。
5. 独立重建与整树比较必须仅两份运行文件变化；默认只读、重复应用无写入、双文件备份/回滚、输入/源文件篡改/混合版本拒绝、语法失败/STALE_FILE/第二文件I/O失败回滚均需验证。
6. 任一门失败，不应用正式目录；保留失败日志并修复/更新文档后重新验证。

```bash
python tools/dspp-readimage-v7-patch.py --check
python tools/dspp-readimage-v7-validate.py --baseline D:/tmp/DeepSeekPP-readimage-v7-20260917/frozen-v6 --output D:/tmp/DeepSeekPP-readimage-v7-20260917/validation
# 全部离线门通过后才执行：
python tools/dspp-readimage-v7-patch.py --apply
# 如需精确回退：
python tools/dspp-readimage-v7-patch.py --rollback
```

机器可读报告/原始日志保存在上述临时目录，不放入docs。

## 6. 浏览器验收

1. 用户保存工作后，在 `edge://extensions` 重载扩展；关闭旧DeepSeek页并打开新页/新会话。
2. 用非敏感小PNG/JPEG调用 `read_image`，无需开启侧栏聊天。状态条运行中不要再发送“继续”。
3. 查看 `dpp_read_image_diag_v7`：期望 `capture → upload_start → upload_ok → request_refs(count>0) → request_ack`。
4. 若失败，先依据新枚举定位阶段；`auth_missing/auth_rejected` 应登录/刷新后重试，不能靠改写权限或伪造token解决。`pow_failed/upload_failed` 需继续抓相应网络证据。
5. 必须看到真实上传返回ID、下一completion引用该ID、模型准确描述未由文字泄露的图像内容，才算完成端到端验收。引用存在并不证明模型已看见。
6. 观察新会话不带旧图、侧栏原开关未变化。不要上传敏感原图作测试。

## 7. 更新记录

- 2026-09-17 批次二/最终收口：候选22/22自动读图组、16/16真实后台边界组、55/55旧扩展套件、38/38工程检查全部通过；报告 `D:/tmp/DeepSeekPP-readimage-v7-20260917/validation/report.json`。两文件已应用，应用后从正式文件再次提取执行22/22与16/16通过。
- 正式content.js=902208 B，SHA `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4`；background.js=654147 B，SHA `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc`。
- 与冻结完整树比对：仅上述两文件内容变化，新增仅两份`.v7_bak`；两个备份均与冻结v6源逐字节相等。manifest及其他扩展文件不变。
- 六个维护代码文件诊断返回0 error/0 warning；两个Python文件AST语法通过。未重载浏览器、未执行真实上传、未改变侧栏设置、未发布ZIP/GitHub、未改Athena运行时/数据库/服务。
- 下一步：用户重载扩展并重开DeepSeek标签页，用`_readimg_src.jpg`等非敏感小图验收；查看新键`dpp_read_image_diag_v7`。若出错，按固定错误枚举定位下一层，不能先宣称端到端修复成功。

- 2026-09-17 批次一：核对双文件v6基线并冻结完整扩展；确认侧栏开关缺省false会造成第二层阻断。提交窄权限/当前tab复核/可信主页面分支/固定错误枚举候选及真实分发链测试、双文件补丁器与验证器；同步工作区交接文档。尚未正式部署、尚未真实HTTP验收。

### 2026-09-17T11:09:53+08:00 · read_image v7 apply

- content.js: 902208 B, SHA `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4`。
- background.js: 654147 B, SHA `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc`。
- 两文件备份为各自 `.v7_bak`（v6）；本操作含双文件语法校验和文档回执。
- 未修改侧栏开关、未重载浏览器、未进行真实图片上传；端到端验收仍待进行。


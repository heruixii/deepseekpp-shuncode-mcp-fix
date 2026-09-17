# DeepSeekPP read_image v6：运行隔离、等待上传与验收记录

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 本轮浏览器验收失败（优先于下方此前待验状态）**：磁盘仍为.36/1.14.0.41，GitHub发布不变；本轮22步/30工具，3次取得图像字节后上传被 runtime_message_unauthorized 拒绝，refs=0，2,168字节也失败。其余直接读图含4次文件不存在、6次网络错误，并非全部success。当前MCP小图复核返回原生image块，不能归因于ShunCode始终剥离。具体后台拒绝子条件及浏览器驻留版本未取证；阻塞仍被记为complete待修。本次仅核查，未改运行代码或发布新版。 详见 docs/mcp-deepseekpp-visual-blocker-20260917.md。
> 部署状态（脚本维护）：v8/.36正式磁盘已更新为1.14.0.41；content e66f24d5…f1ec，policy c8e843c8…c8c6，background不变。浏览器重载/新模型验收待进行，分发回执见v8文档；2026-09-17。

> **2026-09-17 v8 当前接手入口**：Fix3.3.10.36 / 1.14.0.41 已部署本机磁盘，修复视觉主动工作流与长未注册工具块误完成；48视觉/22读图/16后台/22原生维护/55旧回归、14工程/6语法通过，正式文件复测48/22/16通过。浏览器尚需用户重载，新模型SVG端到端未验证；GitHub已正式发布 Latest v1.14.0-fix3.3.10.36，提交16a9219ff8dbd3601fedecfb459d1d5431e04248；三个远端附件下载SHA-256及API digest一致。黑曜石已将奇思妙想整理为dspp：4当前入口+21历史原稿+1历史索引，53处链接修复、131处校验，原始备份保留，未推送私人笔记库。详见 docs/mcp-deepseekpp-visual-workflow-v8.md。下方旧版状态按历史阅读。

## 当前状态（2026-09-17）

> 历史（v7修复前）：2026-09-17 最新实测：3043 B图片已捕获；upload_start→upload_failed仅2ms，下一轮ref count=0。抽取真实background权限门复跑，DeepSeek内容脚本调用UPLOAD_DEEPSEEK_IMAGE必被runtime_message_unauthorized拒绝，上传处理器未进入。上一版22/22模拟上传测试漏掉真实sender权限边界；离线通过不等于链路可用。本次仅取证/更新文档，未改运行代码。详见 `docs/mcp-deepseekpp-readimage-upload-boundary.md`。

本轮获用户授权修复自动读图，并要求每次更改同步文档。当前文档是 v6 的实施与验收入口。

- 基础正式版本：manifest `1.14.0.39` / Fix `3.3.10.34`；v6 是本地功能补丁，不是新正式发行版。
- 实施与离线验证已完成，当前磁盘状态以页首“脚本维护”行为准；本轮正式应用与各批次回执保留在文末。专项22/22组、既有回归55/55套件、工程安全检查30/30通过。
- 浏览器端到端状态：**已实测失败**，上传被后台命令权限边界阻断；失败根因与后续修复边界见 `docs/mcp-deepseekpp-readimage-upload-boundary.md`。旧离线测试结果保留，但不代表浏览器可用。
- 不操作 Athena VN 数据库、LLM 配置、TTS 或生产服务；不自动发布 ZIP/GitHub，不关闭浏览器。

## 1. 已核实的基线与代码证据

扩展根目录：`D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`。

| 文件 | 大小 | SHA-256 |
|---|---:|---|
| content-scripts/content.js（v5） | 892202 | `6ba876bd3b2cfa3f6328c328621d43d259a83f5298bb3f68d50ea21f9fe5c54b` |
| content-scripts/content.js.v5_bak（原始 .34） | 890814 | `6657748d6d644b32e288aa7264283122402950c920450d652293c3b9720b5962` |
| background.js | 651417 | `ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32` |

`.dspp_bak/.v4_bak/.v5_bak` 三份原始备份哈希相同。内存中撤销 v5 两处补丁后，与原始备份逐字节一致。当前 v5 的零基 UTF-8 字节偏移：B=`506409`，A=`576270`；旧的 `505957/575617` 不适用于当前文件。所有后续补丁使用哈希和唯一字符串锚点，不使用数字偏移。

### 真正的调用链

1. `J$()` 把手动调用已完成的工具结果放进 payload `toolExecutions`，启动 `i1 → eB → Jz`。
2. `Jz` 初始化 `g=[...t.toolExecutions]`。这些首次结果不重新触发 SDK 的 `tool_execution_end`，所以只改该事件会漏读。
3. Agent 内新调用经 `Uz` 返回 `{content:[text summary], details:f.result}`。`i1` 的执行封装明确保留 `result.output`；图像可能位于 `details.output` 的 MCP 内容/结构化结果，而不是顶层 `e.result.content`。
4. `Jz` 的 `Te` 是 async 事件处理器，SDK `nP` 等待该回调；可在结果完成事件内等待捕获/上传。
5. Web 提交链是 `Jz → JR → VR → BR → HR → Hc`，实际 JSON 字段为 `ref_file_ids:e.refFileIds`。
6. v5 的 `sendMessage` 回调没有等待机制，`DPP_RIF` 是无会话隔离全局队列，且请求构造时提前 `splice(0)` 消费，网络失败可丢引用。

这些是静态可复现的代码缺口，不能单凭它们声称已重现浏览器现场全部失败原因。

## 2. 目标、非目标与不变量

目标：Web Agent 首次结果和循环内结果均能在下一次真实 completion 前完成图片上传并携带引用；失败有明确状态，不把“文件已读”冒充“模型已看见”。

必须保持：

- 完成门、capability 一次性语义、手动接管、DOM 保险丝、结果增量回灌等 .30–.34 机制不改。
- 官方 API 通道不改为图片通道，不新增 API key/模型/外部图析服务。
- 复用既有 `UPLOAD_DEEPSEEK_IMAGE` 与上传鉴权/PoW；background.js 不改。
- 既有用户附件引用不改动、不抢占；`DPP_AGENT_SYNTHETIC_REF_FILES_337` 保持原空数组，不把它变成新的全局队列。
- 只处理 `read_image`、其 MCP 名称后缀及 `mcp_invoke` 结果中的结构化图片；不扫描 read_files/命令输出中的图片字面量自动上传。
- 不扩大 MCP 响应上限、不改 ShunCode runtime、不自动重载浏览器。

## 3. 数据流、容量与失败行为

每个 `Jz` 运行创建独立 `DPP_CREATE_READIMAGE_V6`：

`首次 g 或新 DPPExecution → capture → 结构化提取/校验 → await 上传 → pending IDs → wrapSubmit → completion finished → 消费已确认的 IDs → finally close`

- 只沿 `result/details/output/structuredContent/content` 包装遍历；支持 MCP text block 的完整 JSON，不从任意自然语言中猜取 JSON。
- 深度≤8、访问≤256；文本解析预算12MiB。PNG/JPEG/GIF/WebP；检查 base64 编码、实际字节数和格式签名。
- 单图片≤8MiB，每次 capture 累计≤8MiB；每批最多4张、pending 最多4个引用；每运行最多16个成功图片哈希。
- 上传批次总等待预算20秒；支持 signal abort。超时/取消后的迟到回调不得进入 pending。由于既有消息接口无单次取消令牌，已发出的后台上传可能继续，但返回值不会污染新运行。
- SHA-256 去重缓存仅活在本运行，不存 base64 缓存。上传成功严格要求 `{ok:true,file:{id:非空字符串}}`。
- 原 `result` 不原地修改；图像结果返回副本，删除二进制字段，保留元数据/普通文字。原始历史 trace 不做迁移/清理。
- completion 网络失败或 `finished !== true` 时保留 pending，允许既有重试使用；仅在完成响应后消费请求快照中的 IDs。会话不匹配时拒绝提交，取消/结束时清空。
- 上传失败继续文字流程，并在下一请求附上有界附件状态；绝不宣称模型已经看到图片。

## 4. 诊断与隐私

新增同源 localStorage 键 `dpp_read_image_diag_v6`，最多64条，仅存时间、版本、stage、数量、字节数等元数据。

阶段包括：`run_ready`、`capture`、`upload_start`、`upload_ok`、`upload_failed`、`upload_timeout`、`cache_hit`、`request_refs`、`request_ack`、`session_mismatch`、容量/格式失败。

不记录像素/base64、完整本地路径、请求正文、凭据、上传响应原文、file ID。已有扩展历史工具日志的行为不在本补丁清理范围内。自动上传意味着所读图片会发送至当前 DeepSeek 账户的文件服务；敏感图片不要用作验收素材。

## 5. 文件级改动与提交批次

### 批次一：候选实现与文档同步

- `tools/dspp-readimage-v6-runtime.js`：独立可读源代码，最终嵌入 content.js。
- `tools/dspp-readimage-v6-patch.py`：从锁定原始 .34 生成候选，仅接受精确 v5 或精确当前 v6；默认检查；`--build` 禁止写正式目录。
- `tools/dspp-readimage-v6-selftest.js`：纯离线浏览器接口模拟，执行候选实际 helper 和实际 `Jz` 事件处理器。
- `tools/dspp-readimage-v5-patch.py`：禁止旧脚本直接应用，只保留 `--check` 历史检查，防止其先回滚再校验的行为覆盖新版。
- 更新三份读图文档的当前入口、过时结论/状态，保留历史取证；工作区新增上传总交接文档镜像并标注当前补丁状态。
- 每批次在 `AGENT_HANDOVER.md` §12 顶部登记，不更改 Athena 顶部生产状态。

### 批次二：验证与正式应用

1. 检查原始备份、v5、background、manifest；不匹配即停止，不覆盖未知文件。
2. 在 `D:/tmp/DeepSeekPP-readimage-v6-20260917/` 构造隔离候选树，禁止以正式目录作为构建目标。
3. 运行专项：首次结果、循环内 mcp_invoke、深层/JSON 图块、时序、大小/MIME、超时/失败/迟到回调、取消/跨会话、引用保留与去重、文本/API 回归、诊断隐私。
4. 按本计划执行扩展自身现有55个 `*-selftest.js` 套件（不运行 Athena 全量测试）；如有失败，先与原始 .34 基线比较，禁止为变绿删断言或擅改版本门。
5. 验证两个独立构建结果字节一致；篡改输入拒绝、重复应用无写入、语法失败无写入；离线临时目录验证 apply/rollback 与文档回执。
6. 全部离线门通过才 `--apply`：预检全部文件、暂存全部新文件、保存精确 v5 为 `.v6_bak`，同步写文档应用回执，最后替换 content.js；I/O 失败尝试回滚。非跨文件系统/断电原子事务。
7. 核对实际目标 SHA/大小、background 未变、文档与诊断，记录验收边界。

## 6. 验证命令

工作目录为 Athena 工作区，Python 使用可用的 Python 3；下列 `D:/...` 传给 Windows Python/Node：

```bash
python tools/dspp-readimage-v6-patch.py --check
python tools/dspp-readimage-v6-patch.py --build D:/tmp/DeepSeekPP-readimage-v6-20260917/candidate-content.js
node tools/dspp-readimage-v6-selftest.js D:/tmp/DeepSeekPP-readimage-v6-20260917/candidate-content.js
# 其余55套件在隔离候选树中执行并保存摘要/原始日志；不会据此直接调用任何模型。
# 离线门通过后：
python tools/dspp-readimage-v6-patch.py --apply
```

构建/应用前会执行 Node 语法检查。脚本不运行 v4/v5 patcher，不把备份覆盖到 live 后才检查。

## 7. 浏览器验收（必须另行完成）

1. 保存工作，`edge://extensions` 重载解压扩展；关闭旧 DeepSeek 标签页，打开新标签页/新短会话。
2. 使用工作区合成的、非敏感小 PNG/JPEG；不要用文件名或工具说明泄露待识别的内容。
3. 第一次回复直接调用 `read_image`（覆盖首次 `toolExecutions` 路径），由 Agent 自动续轮，无需用户再发消息触发。
4. 再在运行中的后续步骤通过 `mcp_invoke` 读取另一张图（覆盖事件路径）；状态条运行中不要发“继续”，避免手动接管。
5. 检查实际 Network：上传成功返回 ID，紧随的 completion 的 `ref_file_ids` 包含相同 ID；诊断 `upload_ok → request_refs → request_ack`。
6. 模型必须准确描述未在文字中泄露的图像内容。**单凭模型说“我看到了”、有 ID、或工具 success 均不算通过。**
7. 新运行/新会话不能带旧图；故障时应看到上传/引用失败状态，不应伪称已识图。

如果端到端仍失败，先定位 `capture` 是否出现、上传业务是否成功、引用是否到达真实请求，再核实服务端对该文件的处理/视觉能力。不重新退回“API input:text 就证明当前 Web 不可行”的旧推断。

## 8. 回滚

```bash
# 精确 v6 -> 本次修改前的 v5，含文档回执；v5 本身仍是已知未成功版本。
python tools/dspp-readimage-v6-patch.py --rollback
# 然后由用户重载扩展并重开标签。
```

原始 .34 在 `content.js.v5_bak`（6657748d…），修改前 v5 在 `content.js.v6_bak`（6ba876bd…），不要混淆。需要回到完全无读图补丁的 .34 时，应重新确认哈希并记录文档，不盲目执行旧脚本。GitHub 工作副本与桌面旧交接文件不自动更新/发布；当前工作区入口是 `docs/DeepSeekPP-Fix3-项目交接文档.md`。

## 9. 更新记录

- 2026-09-17 收口：正式 content.js 已应用 v6，**901444 B**，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`；background 未改。最终隔离报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation-final/report.json`：专项22/22组、旧回归55/55套件、工程检查30/30；应用后实际目标专项再次22/22。5个维护代码文件诊断返回0 error/0 warning，3个Python文件语法通过。原始 .34 `.v5_bak` 与修改前 v5 `.v6_bak` 均已核验。未重载浏览器、未实际上传图片、未发布GitHub/ZIP；端到端识图仍待用户验收。

- 2026-09-17 批次三：隔离验证已通过：实际 helper/Jz **22/22 组**、扩展既有 **55/55 套件**，独立重建一致且树差异仅 content.js；默认只读、重复应用无写入、精确备份/回滚、输入/运行源篡改拒绝、坏语法拒绝、STALE_FILE 与模拟 I/O 失败回滚均通过。报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation/report.json`。追加部署状态自动维护行及其 apply/rollback 断言，避免未来回滚后页首仍称 v6 已部署；正式应用前再验证此维护逻辑。

- 2026-09-17 批次二：首个候选实际 helper + Jz 专项 **22/22 组通过**，Node 语法通过；候选 901444 B，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`。增加 runtime/output 哈希锁、文档读取版本快照保护和独立离线验证器（55 个扩展旧套件 + patcher 篡改/回滚/事务故障测试）；接下来执行这些门。正式 content.js 仍为 v5；未重载/上传。

验证器命令：`python tools/dspp-readimage-v6-validate.py --output D:/tmp/DeepSeekPP-readimage-v6-20260917/validation`；该目录必须尚不存在，日志与 JSON 报告留在 docs 外。

- 2026-09-17 批次一：完成调用链取证，修正旧偏移和初始结果/时序假设；提交候选实现、专项测试和维护脚本，同步更新交接文档。正式扩展仍为 v5；浏览器验收未进行。

### 2026-09-17T10:48:39+08:00 · read_image v6 应用

- content.js: `6ba876bd3b2cfa3f6328c328621d43d259a83f5298bb3f68d50ea21f9fe5c54b` → `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`，901444 B。
- 回退备份：`D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3/content-scripts/content.js.v6_bak`；background.js 保持 `ed5751c7dfa819e51bb8df24beea990c505db7eb6f7c3654fa58217177844f32`。
- 本操作通过 Node 语法预检；离线行为测试见 v6 专项文档。
- 未自动重载扩展、未执行真实图片上传、未发布 GitHub/ZIP；浏览器端到端验收仍待进行。

### 2026-09-17T11:09:53+08:00 · read_image v7 apply

- content.js: 902208 B, SHA `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4`。
- background.js: 654147 B, SHA `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc`。
- 两文件备份为各自 `.v7_bak`（v6）；本操作含双文件语法校验和文档回执。
- 未修改侧栏开关、未重载浏览器、未进行真实图片上传；端到端验收仍待进行。


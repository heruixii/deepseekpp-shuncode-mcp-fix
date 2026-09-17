# DeepSeek++ 扩展修复项目 · 交接文档

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 15:51 当前接手入口（优先于下方全部旧状态）**：本机 live `D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` 已运行 **Fix 3.3.10.40 / 1.14.0.45**；GitHub 已发布 **`v1.14.0-fix3.3.10.40`（Latest）**：ZIP `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.40.zip` 9,109,365 B SHA-256 `8b40e9ff…b358`，99 个运行时文件与验收候选逐字节一致，回退点 `D:\tmp\DeepSeekPP-Fix331036-pre331040-20260917`。.36 的浏览器视觉上传阻塞（`runtime_message_unauthorized`）已由 **.38** 修复并验收通过：根因是 `DPP_REQUIRE_UPLOAD_CONTEXT_V7` 拿冻结于文档提交时刻的 `sender.url` 会话段与 `tab.url` 比较（.37 诊断现场命中 `ctx_sender_tab_session_mismatch`），现改以浏览器 tab URL 为准并锁定监听时会话，其余检查全部保留；浏览器三次 `upload_ok→refs=1→ack=1`。.39 加 MAIN-world 直写诊断 `dpp_mw_bridge_diag_v10`；.40 修 `main-world.js` 技能弹窗 `observe(null)`。每级都有 hash 锁 builder/validator（`tools/apply-fix33103[7-9|40].py`、`validate-…`），基线须用干净 .36 树 `D:/tmp/deepseekpp-base36`；每级 live 备份与回执在 `D:/tmp/deepseekpp-fix33103N-20260917/`。待办：(a) 已完成发布（`docs/RELEASE-Fix3.3.10.40.md`）；(b) 15:1x 曾出现一次“新对话首条消息无工具、扩展零日志”未复现，再现时读 `dpp_mw_bridge_diag_v10`；(c) 黑曜石 dspp 未同步 .37–.40。详见 `docs/mcp-deepseekpp-visual-blocker-20260917.md` §9–§14、`docs/mcp-deepseekpp-upload-gate-fix38.md`、`docs/mcp-deepseekpp-mw-bridge-diag-v10.md`、`docs/mcp-deepseekpp-skill-popup-observe-fix40.md`。

> **2026-09-17 21:4x 当前接手入口（优先于下方全部旧状态）**：live 已是 **Fix 3.3.10.42 / 1.14.0.47**。`.41` 发布后 20:53–20:56 同会话三次 `unexecuted_work_limit_331036` 复现，取证发现**根因在暴露层而非提示词**：`fix3-policy.promptExposureSettings` 把 ShunCode（15 工具 35,883 B > 28,000）从 direct 悄悄降为 adaptive（5 槽/14 KB），每轮按关键词重选，「继续」时 read_image 权重 0、视觉提示时 run_command 被挤掉，模型调用的总是上一轮还在的工具；裸标签别名（方案 D）对此无效。`.42`：触发线 48000 + 尊重显式 direct + adaptive 8 槽/24 KB + read_image floor 1000 + turn_diag 白名单加 `resolution`。证据与回执：`docs/mcp-deepseekpp-exposure-drift-fix42.md`。builder/validator `tools/*-fix331042.py`（22 checks/69 进程/57 套件全过，fail-closed 三项验证）。回退点 `D:/tmp/DeepSeekPP-Fix331041-pre331042-20260917`。**浏览器未验收**；发布状态见 §7 末条。

> **2026-09-17 20:5x 当前接手入口（优先于下方全部旧状态）**：`.41` 已发布（Latest）且浏览器验收通过；本条只做收尾：①黑曜石 `dspp/00`–`03` 已同步到 .41/1.14.0.46（备份 `dspp/_backup-20260917-fix41/`，私有库不推送）；②仓库工作树 3 个未跟踪 `.bak-*` 文档备份移入 `local/_doc_backups_20260917/`（gitignored）；③桌面副本 `C:\Users\29066\Desktop\DeepSeekPP-Fix3-项目交接文档.md` 已用本文件覆盖（仅镜像，真源仍是仓库）；④§0 TL;DR 已更新到 .41。**运行代码未改、未发新版**。剩余观察项见 §0「下一步」。

> **2026-09-17 17:0x 当前接手入口（优先于下方全部旧状态）**
>
> - **已完成**：**Fix 3.3.10.41 / 1.14.0.46 已部署到 live**（216 文件），修复裸 ShunCode 工具标签导致的 `unexecuted_work_limit_331036` 空转停止。只改 `content.js`；background / main-world 与 .40 逐字节一致。
> - **验收**：新专项 34/34；`validate-fix331041.py` **passed:true**（31 checks / 69 processes / 56 suites）；v8 48/48；live 全量 56/56；三类篡改均 fail-closed；独立重建 228/228 零差异。
> - **产物**：`content.js` SHA `fabe7c7ca8283044caf31c909398f53f74d8d6be189b21d4f3a9c9463f16cb01`；回退点 `D:/tmp/DeepSeekPP-Fix331040-pre331041-20260917`（.40 冻结 215 文件）；工具 `tools/apply-fix331041.py`、`validate-fix331041.py`、`dspp-bare-tool-tag-v41{,-selftest}.js`、`fix331041-source-sha256.json`。
> - **浏览器验收：已于 19:53 通过**（loop `924059bb`：`task_complete`、5 步 5 工具、read_image 真实执行 ok=True、裸标签 0 次、`unexecuted_work_limit_331036` 17:00 后零条）。快照 `D:/tmp/edsnap-331041-verify-20260917`，详 §6.5。原待办 —— 重载扩展 + 关旧标签开新页，跑参考图任务；期望 `unregistered_tool_tag_331033` 的 `resolution=exact_hint`、不再出现 `unexecuted_work_limit_331036`、出现 `dpp_read_image_diag_v7` 的 `upload_ok→refs→ack`。**未打 ZIP / 未打 tag / 未发 Release**（需授权）；黑曜石 dspp 未同步 .41。
> - **实施中的关键经验（后人必读）**：v8 套件会把 `DPP_VISUAL_RULES/RETRY_331036`、`vo()`、`shouldStopAfterTurn`、`DPP_UNREGISTERED_TAG_STEERING_331033` **分别抽出单独 eval**，任何外部 helper 引用都会 `ReferenceError`（本轮踩中 4 次）。四处改点均已**内联自包含**，validator 新增 `no_external_v41_ref_in_eval_regions` 固定该约束。另：注册名匹配**不写死 serverId 段数**（任务书原定 `{4}` 会在换 server 时静默失效）。
> - **详见**：`docs/mcp-deepseekpp-bare-tool-tag-fix41.md` §6 回执。

> **2026-09-17 16:30 当前接手入口（优先于下方全部旧状态）— 交给下一个智能体**
>
> - **已完成**：.40 / 1.14.0.45 已部署且 GitHub Latest（见下一条 15:51 入口）；黑曜石 dspp 已同步 .40。
> - **当前问题（已取证、未修复）**：浏览器任务反复以"DeepSeek 连续 3 次明确表示要调用工具，但仍未输出可执行 tool call"停止。16:00 五次中断**全部**是扩展侧 `unexecuted_work_limit_331036`，**无一网络原因**。根因：模型对读图裸写 `<read_image>`（注册名其实是 `mcp_t_…_read_image`），.33 未注册标签检测器命中后，.36 视觉提示词仍用裸名要求调用、.33 纠偏文案又叫它去 `mcp_discover`（工具明明已在目录），提示自相矛盾，3 轮纠偏后被安全停止。
> - **解决方式（.41，待实施）**：纠偏文案改为给出精确注册标签；视觉规则/重试文案注入真实 read_image 名；新增 `resolution` 枚举诊断。不触碰授权检查。完整方案、自测清单、实施与验收步骤见 **`docs/mcp-deepseekpp-bare-tool-tag-fix41.md`**。
> - **下一个智能体阅读顺序**：① 本文档顶部两条入口 + §4 发布规范 + §7 末三条更新记录；② `docs/mcp-deepseekpp-bare-tool-tag-fix41.md`（任务书）；③ `docs/mcp-deepseekpp-visual-workflow-v8.md`（.36 视觉规则原始设计）；④ `docs/mcp-deepseekpp-visual-blocker-20260917.md` §9–§14 与 `docs/RELEASE-Fix3.3.10.40.md`（.37–.40 链路和打包方式）；⑤ 代码入口 `tools/apply-fix331040.py`、`tools/validate-fix331040.py`、`tools/dspp-visual-workflow-v8.js`、`tools/dspp-unregistered-tag-v8.js`。黑曜石 `dspp/02`、`03` 仅在维护黑曜石时读。
> - **硬约束**：基线只能用 `D:/tmp/deepseekpp-base36`；builder/validator hash 锁 + fail-closed；发版前冻结回退点；新诊断只记固定枚举/布尔；不删弱授权检查；发布/打 tag 需用户明确授权；不重发 .36/.40；不动 Athena 目录；黑曜石不推送。

> 历史（已被 .38 修复）：**2026-09-17 本轮浏览器验收失败**：磁盘仍为.36/1.14.0.41，GitHub发布不变；本轮22步/30工具，3次取得图像字节后上传被 runtime_message_unauthorized 拒绝，refs=0，2,168字节也失败。其余直接读图含4次文件不存在、6次网络错误，并非全部success。当前MCP小图复核返回原生image块，不能归因于ShunCode始终剥离。具体后台拒绝子条件及浏览器驻留版本未取证；阻塞仍被记为complete待修。本次仅核查，未改运行代码或发布新版。 详见 docs/mcp-deepseekpp-visual-blocker-20260917.md。
> 部署状态（脚本维护）：v8/.36正式磁盘已更新为1.14.0.41；content e66f24d5…f1ec，policy c8e843c8…c8c6，background不变。浏览器重载/新模型验收待进行，分发回执见v8文档；2026-09-17。

> **2026-09-17 v8 当前接手入口**：Fix3.3.10.36 / 1.14.0.41 已部署本机磁盘，修复视觉主动工作流与长未注册工具块误完成；48视觉/22读图/16后台/22原生维护/55旧回归、14工程/6语法通过，正式文件复测48/22/16通过。浏览器尚需用户重载，新模型SVG端到端未验证；GitHub已正式发布 Latest v1.14.0-fix3.3.10.36，提交16a9219ff8dbd3601fedecfb459d1d5431e04248；三个远端附件下载SHA-256及API digest一致。黑曜石已将奇思妙想整理为dspp：4当前入口+21历史原稿+1历史索引，53处链接修复、131处校验，原始备份保留，未推送私人笔记库。详见 docs/mcp-deepseekpp-visual-workflow-v8.md。下方旧版状态按历史阅读。

> 历史（v7修复前）：**2026-09-17 当前接手状态（优先于历史段落）**：基础 `.34 / 1.14.0.39` + read_image v6 已写盘；浏览器实测失败。2026-09-17 最新实测：3043 B图片已捕获；upload_start→upload_failed仅2ms，下一轮ref count=0。抽取真实background权限门复跑，DeepSeek内容脚本调用UPLOAD_DEEPSEEK_IMAGE必被runtime_message_unauthorized拒绝，上传处理器未进入。上一版22/22模拟上传测试漏掉真实sender权限边界；离线通过不等于链路可用。本次仅取证/更新文档，未改运行代码。详见 `docs/mcp-deepseekpp-readimage-upload-boundary.md`。 当前副本位于工作区；桌面/GitHub旧文档未同步。

> **这份文档是项目的唯一交接入口。每次对项目做任何改动（修复、发版、验证、结论更新）后，都必须更新本文档**（改对应章节 + 在文末「更新记录」追加一条），保证任何人接手都能从本文档直接进入状态。
>
> - 创建时间：2026-09-16
> - 创建方：Arena Agent（经 ShunCode Bridge MCP 连接本机）
> - 信息来源：ChatGPT 分享对话《分析页面崩溃原因》(https://chatgpt.com/share/6aaa2f87-4e60-83ee-86c1-63215ea6b70d) + 本机工作区 `D:/tmp/gh-deepseekpp`

---

## 0. 一页速览（TL;DR）

| 项目 | 状态 |
|---|---|
| 在做什么 | 修复 **DeepSeek++ 浏览器扩展**在自动化执行任务时导致 **DeepSeek 网页崩溃 / "服务器暂不可用" / 任务中断** 的系列问题 |
| 当前正式版 | **`1.14.0.47 / DeepSeek++ ShunCode MCP Fix 3.3.10.42`**（live 已写入，217 文件；GitHub 发布状态见 §7 末条） |
| 正式目录 | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`（Edge 解压加载） |
| 最新成就 | **“继续/重试只口头答应不调工具”根因实锤并修复**：MCP 传输故障被完成门当作有效进展 → trace 误标 `complete` → 恢复网关永久拒绝接管；`.31` 双点修复（见 §2.5） |
| 当前阶段 | **Fix 3.3.10.42 已部署 live，待浏览器验收**：.41 后 20:53–20:56 三连断的真实根因 = 工具暴露漂移（ShunCode 15 工具 35.9 KB > 28 KB 自动降级线 → 被悄悄改成 adaptive 5 槽，每轮工具表随提示词漂移，模型调用上一轮还在的工具）。.42 改暴露层（policy/background）+ 修 .41 `resolution` 白名单 bug |
| 下一步 | ①**用户实测 `.42`**（重载扩展 → 关旧标签 → 新会话 → 参考图任务 + 「继续」；判据 `web_response_diag.descriptorCount==24`、无 `unexecuted_work_limit_331036`）；②旧观察项：首次 read_image `mcp_tool_result_error`、GPU 141、整值重写通道分片化 |
| 如果复现 | 对 Agent 说 **“查看新日志”**。崩溃自查：console 有无 `NotFoundError` 刷屏、`localStorage["dpp_dom_fence_diag_331030"]` 计数是否在涨；**“只口头答应不调工具”自查**：看 `dpp_inline_agent_traces` 末条 `status` 是否 `complete` 且末步无 `toolExecutions` |
| 当前回退点 | `D:\tmp\DeepSeekPP-Fix331041-pre331042-20260917`（.41 冻结版，216 文件）；更早 `…Fix331040-pre331041…`、`…Fix331036-pre331040…` |
| 最新进展 | `.32` 实测失败（继续→零工具 complete / 中途 error）根因实锤 = **run_command 未进直连集 + 句柄别名残留 + 完成门零工具盲区**（§2.7）；`.33` 实测：Agent 本身正常，“只跑一会就中断”= **用户在运行中发新消息触发 .33107 手动接管**（§2.8）；`.34` 修假失败 + 中断可见 + 用户指南，已发布 |

---

## 1. 项目概况

### 1.1 生态组成

- **Athena 计划**（ShunCode 工作区 `D:/tmp/gh-deepseekpp`）：桌面 AI 助手主项目（`main.py`、Live2D、GPT-SoVITS TTS、wxauto 微信自动化等目录）。MCP Bridge 默认工作区即此目录。
- **DeepSeek++ 扩展（deepseek_pp）**：Edge 浏览器解压扩展，增强 DeepSeek 网页版——自动化任务队列、网页 Agent 连续执行、经 **MCP capability / mcp_invoke** 调用本机 ShunCode 工具、提示词/记忆注入、usage 统计、trace 诊断等。这是本修复工程的主体。
- **ShunCode Bridge**：把 IDE/Agent 能力桥给网页 Agent，扩展崩溃问题长期集中在**网页 Agent / 恢复上下文**链路，而非 Bridge 本身。

### 1.2 关键路径

| 用途 | 路径 |
|---|---|
| 正式扩展目录（Edge 加载此目录） | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` |
| 正式 ZIP（当前 .32） | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.32.zip`（13,920,096 B，204 文件） |
| 当前 ZIP SHA-256 | `7C52B0C5721CD63CC4ACA4A3DF07A986F980DD6508ACC2BE55FB7324BD100D8C` |
| 回退点（每次发版前冻结上一版） | `D:\tmp\DeepSeekPP-Fix3310XX-pre3310YY-20260916` |
| 工作区（Athena） | `D:/tmp/gh-deepseekpp` |
| 稳定化计划 | 项目内的稳定化计划文档，每版追加一节，目前到 **第 27 节** |

---

## 2. 问题全景与根因结论（已查实的）

### 2.1 原始症状

自动执行多个连续任务时：①网页"服务器暂不可用"；②页面崩溃；③任务执行中断，页面残留 `<tool_invoke> {...} </tool_invoke>` 原文；④前 1~2 次失败、第 3 次玄学成功、第 4 次又断。

### 2.2 分层根因（重要：不是单一问题）

1. **"服务器暂不可用"的真相**：DeepSeek 后端**生成阶段返回 `generation_err`（INCOMPLETE）**，HTTP 其实是 200 + SSE；页面笼统显示成"服务器不可用"。属于服务端临时生成失败，自动重试可以成功。
2. **上下文雪崩（页面崩溃主因之一）**：网页 Agent **每一步**都把从任务开始**累计的 ShunCode 工具结果**重新塞进下一轮 `<tool_results>`/`prompt`，服务端又保留前轮历史 → 会话体积持续叠加；系统提示词 + 约 39 KB 的 MCP 工具 schema 每轮全量注入进一步放大。实测会话膨胀到 **~196K tokens**。
3. **前端压力**：长寿命 renderer（SPA 切会话不重启渲染进程）中，扩展用 TreeWalker 反复扫描/清洗超长 DOM 与工具标记；恢复 60~90 KB 的 trace UI，最终把 renderer 推向崩页。
4. **"继续"恢复链**：用户发"继续"后页面崩溃，崩溃点在新请求真正进入 completion 之前的前端恢复逻辑（resume/checkpoint 路径）。
5. **Agent 执行逻辑 bug 群**（逐一修复）：
   - 模型声称要调工具但只输出计划 → 原先只允许 1 次纠偏 nudge，然后落 `EMPTY_FINAL` 误判结束；
   - 拿到新 `run_command` capability 后模型连续只说"我要调用工具"，撞 `tool_intent_limit`；
   - `<tool_invoke>` 文本没被 parser 识别为真实工具调用，原文残留页面（capability 调用协议兼容问题）；
   - 中间有 11 次工具调用 ≠ 任务成功：最后输出"继续读取剩余内容"被错误标记 `complete`；
   - 空 PTY 后重放同一 capability、`mcp_invoke` 后旧 capability 未失效等状态机问题；
   - `.15` 诊断链自身 bug：DeepSeek completion 走 **XHR**，而诊断只钩了 fetch，且 XHR terminal 缺 requestId 导致 `REQUEST_TERMINAL` 被丢弃（`.16` 修复）。
6. **持久化写压力（.29 处理）**：任务结束附近 Extension LevelDB 一次写约 **975 KB**：usage 历史 ~536 KB（`deepseek_pp_usage_turns_v1` 单键、约 1486 条记录、每次 flush 整数组重写，恰在任务完成 ~15 秒后，对应旧 15 秒 flush 定时器）、Agent trace ~252 KB、tool history ~131 KB、turn diagnostics ~55 KB。
7. **GPU/WATCHDOG**：崩溃附近 Windows 记录 `LiveKernelEvent 141`，但引用的仍是**旧的 8 月 `WATCHDOG-20260821-1127.dmp`**（同一 Report ID 重复上报），Edge Crashpad 无新 dump。**只能算可疑信号，未证实是新 GPU TDR；未改动硬件加速或系统设置。**

### 2.4 页面崩溃根因·已实锤（2026-09-16 下午，CDP 现场抓获 + 用户裁定：**扩展恢复注入与 DeepSeek React 互撞**）

**机制链（每一环都有证据）**：

1. 硬刷新重负载会话（如 `c0ba574e-2a70-447a-8551-fe2031d0d965`）时，扩展恢复路径把工具块/agent 轨迹（`.dpp-tool-block` / `.dpp-agent-container`）注入 DeepSeek React 管理的 `.ds-message` 容器；
2. DeepSeek 前端 reconciler（fe-static bundle 内函数 `su`）按 fiber 树计算锚节点执行 `Node.insertBefore`，锚点已被注入节点移位 → 抛 `NotFoundError: Failed to execute 'insertBefore' on 'Node'`（CDP console 连续捕获 ≥5 次，存 `D:\tmp\hang_capture.json`）；
3. 未捕获异常命中 DeepSeek 应用层错误边界 → 整树换成「页面崩溃 / 刷新重试」错误屏（实截图 `D:\tmp\probe_page.png`：标题残留会话名、`dsMessages=0`、扩展在场 `dppStyleNodes=4`）；
4. **反直觉关键点：renderer 进程没死**——CDP evaluate 探活正常、`Inspector.targetCrashed` 未触发、无新 Crashpad dump。这是**应用层"假活真崩"**，只看进程死活必漏判；
5. SPA 应用内切换不重新执行恢复注入竞态 → 不崩。与用户观测"切换没事、刷新必崩"完全吻合。

**排查过程（诚实边界）**：先排除软件链（13:52–13:55 窗口：HTTP 200 / SSE FINISHED / 无 generation_err / nudge→tool_call 链正常 / tokens 42K→47K 无雪崩 / usage v2 正常）；再用 CDP 240s 监视（`D:\tmp\capture.py`，沙盒配置 `D:\tmp\edgeprobe`，navigate + 自动 reload）抓到上述现场。无扩展对照组（probe2）因运行中实例的 Cookies 无法复制、guest 态无效而未跑成，**用户直接裁定"是扩展注入互撞"**，对照实验终止、不再补跑。

**GPU 141 归位（修正本节上一版的定性）**：13:53 之后整个下午崩溃波**没有新增 LiveKernelEvent 141**，renderer 也无 targetCrashed → 141 与"刷新崩溃"**不是同一问题**，降级为机器级独立观察项（§5 的 A/B 仍建议做，但不再是本 bug 的前置条件）。此前"GPU 堆栈高度可疑"的定性作废——当时还没有看到 app 层错误屏，教训是**"evaluate 探活正常 ≠ 页面正常"，必须看 DOM/console**。

**修复：Fix 3.3.10.30「DOM 保险丝」**（见 §3 表）：MAIN world 于 document_start（先于页面一切脚本）包裹 `Node.prototype` 三个方法，**只吞 NotFoundError**、其余异常原样上抛；就地恢复语义：锚点外源 → 向目标父节点 append；被删节点已摘除 → no-op；挂在他处 → 从真实父节点摘除；`replaceChild` 失效 → 退化为 append。节流 beacon 写 `localStorage["dpp_dom_fence_diag_331030"]`，幂等防重，正常路径零成本。

**软件侧真实遗留（非崩溃根因，排期候选 .31）**：剩余整值重写通道分片化：`dpp_agent_turn_diag_331021`（17 次 ≈941 KB）、`deepseek_pp_tool_history`（≈774 KB）、`dpp_inline_agent_traces`（≈568 KB）、`dpp_tool_execution_blocks`（≈254 KB）、`dpp_agent_tool_shape_diag_331018`（≈130 KB）。

**保留证据（13:50–13:55 软件链取证小节，结论"根因不在数据/网络层"依然成立）**：

- `dpp_web_response_diag_331015`：全部 HTTP 200、SSE FINISHED、无 errorMessage、无 generation_err。
- `dpp_agent_turn_diag_331021`（80 条）：errorName 全空；nudge → reemit_tool_call → tool_call 恢复链正常；loop `a5d1fb38` 推进到 step 8。
- tokens 42K→47K 无雪崩；usage v2 分片正常；v1 536 KB 大键仅被写 1 次（只读兼容生效）。
- Crashpad 无新 dump；Edge 主进程 13:50:32 后未再重启；当天 LiveKernelEvent 141 共 10+ 次（最后一次 13:53:07，P2/P3 恒定），与下午崩溃波无时间相关性。

### 2.5 任务中断后“继续/重试只口头答应不调工具”根因·已实锤（2026-09-16 晚，LevelDB 新日志取证）

**现象**：长任务跑到一半突然中断；用户发“继续”或点“重试”，模型只回一句“好的，我继续/重试诊断命令”，然后直接结束，不再发起任何工具调用。

**取证**：快照 `D:\tmp\edsnap-331030-nudge-20260916`（源 `Local Extension Settings\kdmpkkahkhdmdhfkdihkopikgcocbpbf`，WAL `000900.log`，16:28 新鲜写入）。

**机制链（每一环都有证据）**：

1. **真实中断源是 MCP 传输失败，不是模型偷懒**。`dpp_inline_agent_traces` 末条 loop `d1e59b46` 的 step1 工具结果为
   `run_command ok=false, error.code="mcp_network_error", message="Cannot reach MCP server at https://<your-mcp-host>/mcp/<your-token>"`。
   即 ngrok 隧道瞬断，Bridge 不可达。
2. **失败被当成“已执行”记入结果集**。工具执行失败后仍作为一条 toolExecution 进入 `g`（累计结果数组），后续 `DPP_COMPLETION_GATE_31(g)` 只看“有没有工具结果”，**不看 `result.ok` 是否为 false**。
3. **模型自述收尾 → 直接判 final**。step2 模型输出“MCP 暂时断连，重试诊断命令。”这句既不含 `<task_complete>`，也不含中段续跑线索，于是
   `Az()`（续跑判定）返回 false → `shouldStopAfterTurn` 走 `return o?q(...):(ie=n,q('final',!0))` 的 **`final` 分支**，循环正常结束。
4. **trace 被写成 `status:"complete"`**。证据：该 trace `status=complete`、`totalSteps=3`、`totalTools=3`，但**末步 step2 的 `toolExecutions` 为空**——“三步三工具、最后一步零工具且全部失败”却记为成功完成。
5. **恢复网关因此永久拒绝接管**。`DPP_RESUME_TRACE_CHAIN_331010` 的过滤条件是
   `status==='error' || status==='stopping' || (status==='running' && 过期)`，**`complete` 不在内**；且函数开头先算出“本会话最近一条 complete 的 updatedAt”作为水位 `a`，只接受 `updatedAt > a` 的候选。
   于是这条被误标 complete 的 trace 既不是候选、又把水位抬到最新 → `DPP_RESUME_PREPARE/LIGHT` 恒返回 `null` → “继续/重试”拿不到任何 `<interrupted_run_checkpoint>`，退化成一次**普通聊天**。模型没有工具续跑上下文，自然只能口头答应一句就结束。
6. **前端侧证据吻合**：`dpp_web_response_diag_331015` 显示 16:23:57 / 16:26:00 / 16:28:29 三次 `route="editMessage"`（即“重试”）均 HTTP 200、`streamFinished=true`、`controlTrail` 为 `FINISHED`，**但 `dpp_agent_turn_diag_331021` 在 16:22:34 之后再无任何 `turn_decision` 记录** —— 确认这些请求根本没有进入 Agent 循环，是普通对话轮。

**关键区分（不要误修）**：
- 这**不是** `.27` 修过的 `tool_intent_limit`，也**不是** `.28` 的“未完成不得标 complete”（那条针对模型自称“继续读取剩余内容”的文本判定）。本次是**工具传输层失败**被完成门当作有效进展，属于 `DPP_COMPLETION_GATE_31` 与 `DPP_RESUME_TRACE_CHAIN_331010` 的**共同盲区**。
- 全程 `errorName` 为空、无异常栈：失败被结构化成 `result.error` 正常返回，**没有抛异常**，所以 `agent_exception_331023` 一片空白，只看异常链会完全漏判。
- 与 `.30` DOM 保险丝无关；本轮无 `NotFoundError`、无页面崩溃屏，`.30` 修复未回归。

**修复方案（候选 `.31`，两处必须同时改，缺一仍会复发）**：

1. **完成门增加传输故障判定**（`content-scripts/content.js`，`shouldStopAfterTurn` 的 `final` 分支前）：
   当本步新增的 toolExecutions 中存在 `result.ok===false` 且 `result.error.code` 属于传输类（`mcp_network_error`、`mcp_timeout`、`mcp_unauthorized`、`capability_expired` 等）时，**禁止**走 `final`，改判 `tool_transport_failure_33131` 并触发续跑纠偏；连续失败达上限则落 **`error`**（而非 `complete`）。
2. **无进展死循环必须落 `error`**（trace 落库处 + `DPP_RESUME_TRACE_CHAIN_331010`）：
   一个 loop 若「工具全失败且末步无工具」则 trace 写 `status:"error"` 并带 `error.code`，使恢复网关可接管；同时把水位计算 `a` 限定为**真正成功**的 complete（末步有成功工具或含 `<task_complete>`），避免误标记录抬高水位挡住后续恢复。

**临时绕过（修复发布前，用户可用）**：MCP 断连后不要点“重试”，改为**新开一轮对话**重新下达任务；或先确认 ngrok 隧道已恢复（浏览器直接访问 MCP URL 应有响应）再继续。


### 2.3 关键区分

- 用户最初怀疑"记忆注入导致崩溃"——查实当时真实设置是 `memoryEnabled=false`、`systemPromptEnabled=true`，**普通记忆注入早已关闭**；罪魁是 **system/tool prompt 每步全量注入 + 累计工具结果反复注入**导致的上下文膨胀。
- 注意：**旧的 ~196K token 对话不会因升级插件而瘦身**，测试必须**开全新对话**，否则污染结果。

---

## 2.6 .31 上线后仍然“只口头答应、不调用工具”（已实证，2026-09-16）

**现象**：任务中断后发“继续”，模型口头答应后零工具结束；有时紧接一次整页刷新然后停止。

**取证方法**：不靠阅读代码，而是从 content.js 中抽出真实函数（自动解析 20 个符号依赖闭包），
用 17:16 失败 loop `098021bb` 的真实文本实跑判定：

| 判定 | 实测 |
|---|---|
| `DPP_TOOL_INTENT_TEXT_331021(reasoning)` | **true** |
| `DPP_TOOL_INTENT_331021(text, reasoning)` | **false** |
| `DPP_SAFE_FINAL_CANDIDATE_331021(...)` | **非 null（被提升为终局）** |

**缺陷 1**：`DPP_TOOL_INTENT_331021` 仅在正文为空、或正文自带线索时才查 reasoning。
失败轮次的 25 字符正文 `midstep/strict/Mz` 全为 false，模型在 reasoning 里明写的 run_command 计划被整条丢弃，
于是不触发 tool_intent 纠偏，`Ee()` 直接把残缺文本提升为终局答案（`totalTools:0`）。

**缺陷 2（使前者不可观测）**：`dpp_agent_turn_diag_331021` 经 650ms 批刷，而
`DPP_DIAG_BATCH_FLUSH_ALL_331022` 只挂在**不被 await 的** `pagehide` 上；
inline agent loop 末尾的 `u&&_1()`（`window.location.reload()`）与之竞态，吃掉了失败现场。
`finally` 里被 await 的只有 `MZ(r)`。

> **更正（重要）**：之前“turn_diag 零新增 → 所以 `.31` 改点 A 从未执行”的结论**作废**。
> 证据只能证明“无法观测”，不能证明“未执行”。

**reload 触发条件**（实测两个失败 loop 均 `RELOAD_WOULD_FIRE=True`）：
`iB()` = web 后端 && 非 budgetPaused && finalText 非空 && 会话可见 && 末步 `responseMessageId` 为正整数。
该行为在 `.30` 字节一致，**非 `.31` 引入**；经用户决定 **保留不动**。

## 2.7 `.32` 上线后“继续 → 说完成但零工具 / 中途 error”（已实证，2026-09-16 晚，快照 `D:\tmp\edsnap-331032-20260916`）

**先说结论**：**不是 .30/.31/.32 回归**（全部 HTTP 200、无 DOM fence、无 transport 失败计数）。三层叠加：

1. **主因·能力暴露**：自适应模式（`background.js` `_d/Sd/Cd`）只按用户提示词关键词选 5 个直连工具；提示词 `继续`/`A` 没有关键词，`run_command` **从未**进入直连集（`web_response_diag` 实测注入的是 `apply_patch/find_files/get_command_output/read_image`）。系统提示词却仍教模型输出 `<run_command>` 原始体 → 解析器无此标签 → 整块当文本剥掉。铁证：turn_diag `textChars` vs trace 可见文本 347→39、196→0、309→0、223→0、268→0、1315→57、657→17、790→31（8 个失败回合全部如此）。
2. **次因·句柄生命周期**：`.19` 别名只在自身 `finally` 里移除；模型直接用 `mcp_invoke` 消费同一句柄后别名残留 → `mcp_capability_handle_replayed`；该码不在 `.31` 传输失败集 → 通用 nudge → 3 次上限 → error（loop `61ad9dfd`）。
3. **三因·完成门盲区**：`<task_complete>` 零工具时 `DPP_COMPLETION_GATE_31` 无条件放行（loop `02f8e7f5`）；剥剩几十字且无意图短语时走 `final`（loop `1eeb8389`）。

**`.33` 修复（A/B1/B2/C1/C2）**、证据表、验证步骤见 `docs/mcp-deepseekpp-capability-exposure.md`。
**未升级前的绕过**：侧边栏 MCP → ShunCode 服务器模式 `adaptive`→`direct`，或固定 `run_command/get_command_output/read_files/apply_patch`。

## 2.8 `.33` 上线后“继续只执行一会又中断”（已实证，2026-09-16 23:12–23:18，快照 `D:\tmp\edsnap-331033-20260916-2319`）

**结论：不是扩展缺陷。** 4 个 loop 全部 `status=stopping / "已停止"`，该状态唯一来源是 `r1()`，由 `DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107` 在手动请求入口 `bZ()` 调用。preflight `mw_send_hook_seen` 时间（23:15:37.159 / 23:16:08.934 / 23:16:44.695 / 23:17:21.098）与各 loop 停止时刻**毫秒级吻合**——用户在每步 10–20 秒的等待期内又发了「继续 / 怎么样了」，每发一次打断一次。此前 13 步 loop `3c8a0592` 全部 `tool_call` 正常，`run_command` 已在直连集（`.33` 生效）。

顺带发现两处真缺陷 → `.34`：**E** `DPP_NORMALIZE_RUN_COMMAND_RESULT_33108` 全文扫 `status=failed`，命令输出含该字样（grep 扩展源码）时 `completed/0` 被判 `run_command_failed`（3 次）；**F** 手动打断只显示「已停止」、无诊断。

取证工具升级：`D:\tmp\ldb_extract.py` 现支持 `cramjam` 解 snappy（需用 Python 3.11：`C:\Users\29066\AppData\Local\Programs\Python\Python311\python.exe`），.ldb 表全量可读（19 键）。详见 `docs/mcp-deepseekpp-manual-supersede.md`。

## 3. 修复历程（Fix 3.3.10.11 → 3.3.10.34）

| 版本 | manifest | 主要内容 | 验证 |
|---|---|---|---|
| .11 | — | （前一轮对话）"继续任务"触发页面故障的恢复网关修复 | — |
| .12 | — | 恢复记忆隔离到 Agent 内部 | 33 组回归、82 JS、164/164 字节一致 |
| .13 | — | **根因修复①**：累计工具结果改**增量**注入；完整历史留在内存供判定/统计 | ZIP `9D1B05…26DC` |
| .14 | — | 恢复路径/长寿命 renderer 扫描链路确认；旧 20 万 token 会话 → 服务端异常 → SPA 不换 renderer 链路定性 | — |
| .15 | — | 网页响应诊断链 `dpp_web_response_diag_331015`；定性"服务器不可用"= `generation_err` | 诊断链存在 XHR bug，.16 修 |
| .16 | 1.14.0.21 | 只修 XHR terminal 的 requestId correlation | 11/11 专项、37 套件、86 JS |
| .17 | 1.14.0.22 | 稳定化推进 | 18/18、38 套件、87 JS、174/174 一致；ZIP `A34F9A…B97E` |
| .18 | 1.14.0.23 | 稳定化推进，稳定化计划写入第 20 节 | 88 JS、176/176；ZIP `9EA5E3…` |
| .21 | — | **tool-intent 专用纠偏通道**：同一步最多 3 次，只针对"明确工具意图但无 toolCall"，绝不猜参数/代执行；普通 nudge 保持保守 | 182/182 一致 |
| .22~.23 | — | 失败恢复、"继续"续跑语义、**Codex 风格 Agent 状态显示重做**（只显示当前动作/是否运行/最近一步/是否需介入，隐藏 DSML、内部 reasoning、无意义控制标记）；新增 `agent_exception_331023 + stackHead` 异常定位 | 详见稳定化计划 |
| .24 | 1.14.0.29 | 深度修复收口 | ZIP `083BDD…` |
| .25 | 1.14.0.30 | 46/46 行为回归；health 增加 reasoning-only escalation / generic multi-nudge / privacy 边界硬检查 | ZIP `42B908…` |
| .26 | 1.14.0.31 | "一直服务不可用"新定性：连续 5 次 HTTP 200+SSE 但流终 `generation_err`；修旧 full/compact 循环，raw passthrough（标记 `mw_generation_err_passthrough_*_331026`） | 192/192；ZIP `A5B914…E1E51`；第 24 节 |
| .27 | 1.14.0.32 | 修两个确定性失败点：①新 capability 后模型空喊意图撞 `tool_intent_limit`；②12 步 11 次工具后"继续读取剩余内容"被误判 complete | ZIP `1B42A0…1C88`（12,848,515 B）；content.js SHA `37C60450…FCCF7B`；第 25 节 |
| .28 | 1.14.0.33 | 验收标准硬化：日志时间戳必须推进；空 PTY 不得重放 capability；`mcp_invoke` 后旧 capability 必须失效；未完成不得标 complete | 196/196；ZIP `CED55E…`；第 26 节 |
| **.30** | **1.14.0.35** | **页面崩溃根因修复**：MAIN-world DOM 保险丝（`DPP_DOM_FENCE_331030`）包裹 `insertBefore/removeChild/replaceChild`，只吞 NotFoundError 就地恢复，节流 beacon `dpp_dom_fence_diag_331030`，幂等零成本；发布链同步维护 `_locales` 显示名与 21 个旧套件版本门 | 专项行为 21/21、全回归 49/49、hash-lock 干净升级、篡改 fail-closed、**199/199 独立重建一致**；核心改动仅 manifest+main-world 两文件；ZIP `E33D2579…A378E`（13,911,078 B） |
| **.29** | **1.14.0.34** | **存储写压力根治**：usage 新记录只写 `v2_meta` + 按天分片 `v2_day_YYYY-MM-DD`，旧 v1（~536 KB）转只读兼容、统计时合并读取，无一次性大迁移；trace/tool-history 预算 128→64 KB；保留 180 天/5000 条规则 | 专项存储行为 24/24 + 边界（>180 天 prune 不回写）、.29 专项 25/25、全回归 50/50、99 JS、health（含"hot writer 不得写 v1"硬检查）、hash-lock 干净升级、篡改 fail-closed、**198/198 字节一致**；ZIP `C83459E9…8D7A`；第 27 节 |
| **.31** | **1.14.0.36** | **中断后无法续跑修复**：①完成门新增传输故障判定，`mcp_network_error` 类失败禁止判 `final`，最多续跑 3 次后置 `oe` 落 **`error`**；②恢复网关 complete 水位改为只计真实成功的 run，误标记录不再挡住接管；同步维护 `_locales` 显示名与 22 个旧套件四种版本门形态 | 专项行为 43/43、全回归 **50/50**、hash-lock 干净升级、篡改/重复打补丁均 fail-closed、**独立重建 201/201 零差异**；核心只改 content.js+manifest；ZIP `B3C9C512…B2F540`（13,893,358 B） |

> 所有版本的完整根因、证据、哈希、回归记录都写在扩展目录内的**稳定化计划**（已到第 27 节）与 `FIX3-TEST-REPORT.md`。

---


### Fix 3.3.10.32（2026-09-16）
- **根因**：reasoning 中已宣告但未发出的工具调用被 `DPP_SAFE_FINAL_CANDIDATE_331021` 提升为终局答案（详 §2.6）。
- **改点 C**：当 reasoning 有工具意图、无 `<task_complete>`、且本轮没有任何 `result.ok===true` 的执行时，**禁止提升终局**。
  转而走 `AGENT_LOOP_ERROR` → trace 存为 `error`（可续跑候选）；且该路径不返回真值，**顺带不触发 reload**。
- **改点 D**：`DPP_DIAG_BATCH_FLUSH_ALL_331022` 改为返回 Promise 并在 reload 前 `await`，保证失败现场可诊断。
- **被否决的方案**：曾先改 `DPP_TOOL_INTENT_331021` 无条件回落 reasoning，**导致 fix331025 / fix331027 回归**
  （两套都固定“可见的具体终局优先于陈旧 reasoning”），已回滚；最终只在提升点动手，两条规则同时成立。
- **验证**：专项 12/12；全量回归 **51/51**（`.31` 基线 50/50）；真实失败 trace 提升 true→false，无关 trace 不变；
  篡改与重复打补丁均 fail-closed；独立重建 203/203 零差异。
- **产物**：`1.14.0.37` / `1.14.0 ShunCode MCP Fix 3.3.10.32`；
  ZIP `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.32.zip`
  SHA256 `7C52B0C5721CD63CC4ACA4A3DF07A986F980DD6508ACC2BE55FB7324BD100D8C`，13,920,096 B，204 文件（两次构建 SHA 一致）。
- **回退点**：`D:\tmp\DeepSeekPP-Fix331031-pre331032-20260916`（`.31` 冻结 202 文件）。


> 注：`.31` ZIP 曾被旧 `_mkzip.py`（输出路径写死）意外覆盖，已从冻结的 `.31` 树重建；新版 `_mkzip2.py` 改为受参数控制且固定时间戳。重建后 `.31` ZIP SHA256 = C50C507A0CD0388A868763970DBCEC2DA5FF9DFEAE20653EF1300B31502B7605，202 文件，内容与冻结树逐文件一致。

### Fix 3.3.10.33（2026-09-16，已发布）
- 根因见 §2.7。改动：**A** `background.js` `Cd()` 核心 ShunCode 工具排名下限（`DPP_CORE_TOOL_FLOOR_331033`：run_command +1600 / get_command_output、read_files +1000 / apply_patch、search_files、list_directory +700）；**B1** 任何 `mcp_invoke` 完成后退役同 capability 的 `.19` 别名；**B2** 句柄类错误码入传输失败集（`DPP_HANDLE_ERROR_CODES_331033`）+ 定向纠偏“重新 discover 后下一轮立即 invoke”；**C1** 未注册工具标签检测（`DPP_UNREGISTERED_TOOL_TAG_331033`，诊断 `unregistered_tool_tag_331033`）视为 tool_intent 并说明“标签被忽略”；**C2** 续行提示词或 reasoning 含意图时零工具 `<task_complete>` 拒绝（`zero_tool_complete_331033` / 上限 `zero_tool_complete_limit_331033`）。
- 发布：正式目录 → 1.14.0.38（206 文件）；`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.33.zip` 13,933,248 B SHA256 `7A398F4F…B795`；回退点 `D:\tmp\DeepSeekPP-Fix331032-pre331033-20260916`；GitHub commit `c99119f`，Release `v1.14.0-fix3.3.10.33`（Latest）。
- 产物：`tools/apply-fix331033.py`（`.32→.33`，5 文件 sha 锁 + 11 锚点 fail-closed，bump 26 套件版本门 + 2 locales）、`fix331033-capability-exposure-selftest.js`（53 断言）。干跑目录 `D:\tmp\DeepSeekPP-Fix331033-dry`：`node --check` 4/4，全回归 **54/54**（.32 基线 51/51）。manifest → `1.14.0.38`。
- 保留：.25/.27 “可见 final 优先”、.31 传输门、.32 安全 final 守卫（新套件断言）。

### Fix 3.3.10.34（2026-09-16 深夜，已发布）
- 根因见 §2.8。改动：**E** `DPP_RUN_COMMAND_STATUS_331034` 只解析 `--- OUTPUT BEGIN ---` 之前的 header（兼容 JSON 转义），无标记才退回全文扫描；**F** `r1(reason)` 接受停止原因，手动接管记录 turn_diag `manual_supersede_331034` 并显示「已被你的新消息中断……等状态栏结束后再发“继续”」；新增 `USAGE-zh_CN.md`（安装/暴露模式/置顶/使用/恢复/取证）。
- 发布：正式目录 → 1.14.0.39（208 文件 + USAGE）；ZIP `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.34.zip` 13,946,628 B SHA256 `ECBCB43D…29FA`；回退点 `D:\tmp\DeepSeekPP-Fix331033-pre331034-20260916`；GitHub `cce959e`，Release `v1.14.0-fix3.3.10.34`（Latest）。
- 验证：新套件 24/24（含现场毒化输出复现），全回归 **55/55**，双重建 208/208 零差异，重复打补丁 fail-closed；patcher 拒绝 dst==src（吸取 .33 教训）。
- 其他排查：`tool_call_incomplete` 8 条为模型侧提前 FINISHED，扩展已正确拒执行，暂不处理；HTTP 0 仅 1 次。

## 4. 发布工程规范（本项目的工作方式，务必遵守）

1. **hash-lock patcher**：每版生成锁定上一版六个核心 SHA 的 `.N → .N+1` patcher；干净输入精确升级，篡改输入 **fail-closed**，绝不允许半升级。
2. **独立重建验收**：builder 必须从冻结的上一版**独立重建**新版，与正式目录**整树逐字节比对**（missing=0 / extra=0 / diff=0）才算通过。
3. **发版前冻结回退点**：上一版完整目录冻结到 `D:\tmp\DeepSeekPP-…-pre…-日期`，正式 health 失败就回退。
4. **稳定化计划**：每版追加一节（根因、证据、机制、验证、最终哈希）。
5. **诚实边界**：不夸大结论（例：.29 明确写了"降低写压力 ≠ 已证明修复浏览器崩溃"）。
6. **测试规矩**：`edge://extensions` 重新加载解压扩展 + **彻底关闭旧 DeepSeek 标签页后开新标签页**（不能只"新建聊天"，旧标签页不重载仍跑旧脚本）；不用超长旧对话测试；验收以**任务最终真正完成**为准，不能拿"中间执行了几次工具"当成功。

---

## 5. 历史下一步工作（.31 时点；当前请先读顶部接手状态）

1. **【先做】`.31` 用户实测验收**：`edge://extensions` 重新加载解压扩展 → **彻底关闭旧 DeepSeek 标签页后开新页** → 跑一个需要多步工具的任务，中途制造 MCP 断连（关掉 ngrok/Bridge 数秒）。**预期**：不再一句“我继续”就结束；应看到自动重试同一工具调用；若连续 3 次失败，任务应停在**错误**状态（非完成），此时恢复网关可接管，隔一会儿发“继续”能真实续跑。验证点：`dpp_agent_turn_diag_331021` 应出现 `tool_transport_failure_331031` / `tool_transport_failure_limit_331031` 决策记录。
2. **【降为观察项】GPU 141 A/B**（机器级，独立于网页崩溃问题；每步后连续跑 2~3 个同等级任务看 WER 是否还新增 141）：
   - **A. 退净串流/安卓模拟器**：完全退出 GameViewer（UU 远程）与 MuMu 模拟器及其后台服务 → 重测。
   - **B. Edge 关硬件加速**：`edge://settings/system` 关闭"使用硬件加速(如可用)" → 重启 Edge 重测。
   - **C. 固定单 GPU**：Windows 设置 → 系统 → 显示 → 图形 → 把 msedge.exe 固定为"节能(Intel)"或"高性能(NVIDIA)"其一 → 重测。
   - 任一步崩溃消失 → 根因收敛；都不消失 → D: 更新 Intel UHD 驱动（2024-01 版本偏旧）/ WinDbg 分析 `C:\Windows\LiveKernelReports` 新 dump（P2/P3 定位挂死模块）。
3. `.30` 验证通过后：回 `.29` 验收闭环（稳定化计划第 27 节收尾），并把 `.30` 补进第 28 节。
4. 排期候选 **`.31`**：剩余整值重写通道分片化（turn_diag / tool_history / inline_agent_traces / tool_execution_blocks / tool_shape_diag，见 §2.4 尾）——按 §4 全套发布链执行。
5. 长期观察项：旧 v1 usage 536 KB 数据的去留（目前策略是只读保留、不迁移）。

---


### 下一步（`.32` 交付后）
0. **`.34` 已发布**。用户须知（已写入 `USAGE-zh_CN.md`）：**Agent 状态条运行中不要发消息**，等结束再发「继续」；若再出现「已被你的新消息中断」即为此情形。下一步 = 用户按指南实测 `.34`；若 turn_diag 出现 `manual_supersede_331034` 以外的异常停止再取证。
0a. （历史）`.32` 根因（§2.7）→ `.33`；实测 `.33`：重载扩展 → 关旧标签 → 新会话 → 发无关键词的“继续”；预期 `web_response_diag` 注入工具含 `run_command`，不再出现 `textChars` ≫ 可见文本的回合。若失败导出 `dpp_agent_turn_diag_331021` 看 `unregistered_tool_tag_331033` / `zero_tool_complete_331033` / `tool_transport_failure_331031`。
1. **用户实测 `.32`**：`edge://extensions` 重新加载解压扩展 → 彻底关闭旧 DeepSeek 标签页 → 开新标签页；不用超长旧对话。
   预期：中断后发“继续”应真正发出工具调用；若仍不调用，本轮应落为 `error` 而非 `complete`，且**不再整页刷新**。
2. 若仍失败：直接导出 `dpp_agent_turn_diag_331021`（改点 D 后应能看到失败轮次的条目），重点看 `terminal_promotion` / `turn_decision` 两个 stage。
3. ~~GitHub 同步仍未做~~ **已完成（2026-09-16 晚）**：`.31`/`.32` 各一个 commit（`49f9fb5` / `e42c61a`）+ README（`495cef7`）+ Release `v1.14.0-fix3.3.10.32`。行尾由仓库 `.gitattributes` 处理（js/md/py/ps1 → LF；manifest/_locales → CRLF），提交前已用 `diff --strip-trailing-cr` 验证核心文件仅行尾差异。工作副本 `D:\tmp\gh-deepseekpp`。

## 6. 排查定位技巧（沉淀的经验）

- **Edge 扩展 LevelDB 做只读快照**再分析（注意 Git Bash 的 `/c/...` 路径 Windows Python 不认，要用 `C:\...`）。
- 诊断 keys：`deepseek_pp_usage_turns_v1`（旧大键）/ `v2_meta`、`v2_day_*`（新分片）、`dpp_web_response_diag_331015`（响应诊断）、`agent_exception_331023 + stackHead`（异常+栈头）、Agent trace / tool history / turn diagnostics。
- 服务端 token 轨迹看 usage 记录 `totalTokens` 增长；每步涨 4k~7k 即注入放大。
- 崩溃证据链：Edge Crashpad 新 dump、Windows WER（`LiveKernelEvent 141` 要看引用的 dmp 是否为本次新文件、Report ID 是否重复）。
- **WER 直接查事件日志更快**（Application 日志无需管理员）：`Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddHours(-26)} | ? {$_.Message -match 'LiveKernel'}`；同一 P2/P3 = 同一挂起引擎。ReportQueue 文件夹与 `C:\Windows\LiveKernelReports` 需管理员。
- **LevelDB WAL 解析器已沉淀**：`D:\tmp\analyze_leveldb.py`（解析 WriteBatch，统计每 key 写入字节/次数）；快照目录 `D:\tmp\edsnap-331029-repro-20260916`；key 值导出 `D:\tmp\keysnap_*.txt`。取快照只需 cp `.log/.ldb/LOG/MANIFEST`，不必锁库。
- 区分"旧标签页没重载"与"新版没生效"：先看有无新会话 ID、诊断 key 是否有新时间戳。

---

## 7. 更新记录（每次改动后在此追加）

> 格式：`| 日期时间 | 操作 | 涉及版本/路径 | 结果/结论 | 后续动作 |`

| 日期时间 | 操作 | 涉及版本/路径 | 结果/结论 | 后续动作 |
|---|---|---|---|---|
| 2026-09-16 | Arena Agent 建立交接文档：抓取并解析 ChatGPT 分享对话（2932 条消息，提取 .11→.29 全部修复线），核对工作区与桌面路径 | 桌面新建本文档 | 文档建立；当前正式版确认为 **1.14.0.34 / Fix 3.3.10.29**，处于"等待 2~3 个连续任务真实验收"阶段 | 用户验收后按结果更新第 0/5 节 |
| 2026-09-16 下午 | Arena Agent 响应"查看新日志，ds 网页端不断崩溃"：快照扩展 LevelDB（`D:\tmp\edsnap-331029-repro-20260916`）、读取全部诊断 key、查 Crashpad/WER/进程时间线/显示适配器 | 未改扩展，仅取证分析；本文档 §0/§2.4/§5/§6 更新 | **阶段结论（后被修正）**：软件链全绿；当时定性 GPU 挂起——CDP 实锤后确认该定性偏了，见下一条 | 见下一条 |
| 2026-09-16 傍晚 | Arena Agent 做 CDP 现场捕获并发布 **Fix 3.3.10.30**：edgeprobe 沙盒 9222 端口、`capture.py` 240s 监视 navigate+reload 会话 c0ba574e；hash-lock patcher `.29→.30`、全链验证、落正式目录、ZIP | 正式目录 → 1.14.0.35；`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.30.zip`（SHA256 `E33D…378E`）；/d/tmp 五核心哈希 `.30` 版已录；本文档 §0/§2.4/§3/§5/§7；`docs/mcp-deepseekpp-gpu141-crash-repro.md` 修订 | **根因实锤**：扩展恢复注入与 DeepSeek React reconciler 互撞 → `insertBefore` NotFoundError → app 错误边界「页面崩溃」屏（renderer 未死，GPU 141 解耦降级为观察项）。验证：行为 21/21、全回归 49/49、篡改 fail-closed、独立重建整树 0 差异；核心改动仅 manifest+main-world 两文件 | ①用户重载扩展+硬刷新原崩溃会话验证（§5-1）；②保险丝 beacon 计数 `dpp_dom_fence_diag_331030` 观察；③GPU A/B 仍建议；④候选 .31 分片化 |
| 2026-09-16 晚 | 用户实测：`.30` 重载后硬刷新原崩溃会话 → **"没问题了"**；Arena Agent 将正式 .30 树同步至 GitHub 仓库 `heruixii/deepseekpp-shuncode-mcp-fix`（含 18 个新自测、19 个 patcher、补 tools/apply-fix331030.py、本文档一并入库），更新仓库描述 | GitHub：deepseekpp-shuncode-mcp-fix；正式目录 `tools/apply-fix331030.py` 入库；本文档 §0/§7 | 网页崩溃修复**实测闭环**。GitHub 自 .16 追平至 .30（37 新文件 + 全树更新）；后续行动接上条 ②③④ |
| 2026-09-16 晚 | Arena Agent 补齐 GitHub 门面：README.md 顶部加 .30 Current release 节（.29 降为 Previous）、创建 Release `v1.14.0-fix3.3.10.30`（Latest）并附 ZIP 资产 | GitHub README（commit `d86f4fb`）；Release 附 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.30.zip`（13,911,078 B，SHA `E33D…378E` 已写入 notes）；正式树/仓库 README 同步更新 | GitHub 门面与代码、交接文档三者一致 | 无（待机事项同前：27 节闭环、GPU A/B、候选 .31） |
| 2026-09-16 晚 | Arena Agent 响应“查看新日志，任务突然中断、继续/重试只口头答应不调工具”：快照新 WAL `D:\tmp\edsnap-331030-nudge-20260916`，解析 traces / turn_diag / web_diag / preflight / tool_shape 五条诊断链 | 未改扩展，仅取证；本文档 §0/§2.5/§5/§7 更新 | **根因实锤**：`run_command` 返回 `mcp_network_error`（ngrok 隧道瞬断）→ 失败结果仍计入完成门 → 模型一句“MCP 暂时断连”被判 `final` → trace 误标 `status=complete` → `DPP_RESUME_TRACE_CHAIN_331010` 只接 error/stopping/过期 running，永久拒绝接管，“继续/重试”退化为普通聊天（editMessage 三次 200 但零 turn_decision） | 实施 `.31` 两处修复；修复前绕过：断连后新开一轮对话而非点重试 |
| 2026-09-16 晚 | Arena Agent 实施并发布 **Fix 3.3.10.31**：按 §4 全套发布链（冻结回退点 → hash-lock patcher → 专项套件 → 全回归 → 独立重建 → 落正式目录 → ZIP） | 正式目录 → 1.14.0.36（202 文件）；`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.31.zip` SHA `B3C9C512…B2F540`；回退点 `D:\tmp\DeepSeekPP-Fix331030-pre331031-20260916`；新套件 `fix331031-transport-failure-selftest.js`；本文档 §0/§3/§5/§7 | **修复已落地**：传输故障不再判 final（最多续跑 3 次后落 error）；恢复水位只计真实成功。专项 43/43、全回归 50/50（基线 .30 为 49/49）、篡改与重复打补丁 fail-closed、独立重建 201/201 零差异；只改 content.js+manifest+2 locales+22 版本门套件 | 用户实测（§5-1）；通过后考虑候选 .32 分片化 |
| 2026-09-16 | 3.3.10.32 | reasoning 已宣告但未发出的工具调用被误提升为终局答案；同时修复 reload 与批刷诊断的竞态（使故障可观测）。回归 51/51，独立重建 203/203 零差异。ZIP SHA256 7C52B0C5…0D8C | 已交付，待用户实测 |
| 2026-09-16 晚 | Arena Agent 将 `.31`+`.32` 同步至 GitHub `heruixii/deepseekpp-shuncode-mcp-fix`：工作副本 `D:\tmp\gh-deepseekpp`，`.31` 取自冻结树 `D:\tmp\DeepSeekPP-Fix331031-pre331032-20260916`（202 文件），`.32` 取自正式目录（204 文件）；README 顶部改 `.32` Current / `.31` Previous / `.30` Historical；创建 Release `v1.14.0-fix3.3.10.32`（Latest）附 ZIP | commits `49f9fb5`（.31，30 文件）、`e42c61a`（.32，31 文件）、`495cef7`（README）、`c3fb35d`（本文档）；Release 资产 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.32.zip` 13,920,096 B，SHA `7C52B0C5…0D8C` 已写入 notes；本文档 §0/§1.2/§5/§7 | GitHub 追平至 `.32`；仓库与正式树逐文件比对：仅 `.gitattributes` 声明的行尾差异，无内容差异；仓库多出 `.gitattributes` 与本交接文档两文件（预期）。踩坑复现一次：Windows Python 不认 `/c/...` 路径（§6 已记） | 待用户实测 `.32`（§5）；`.31` 未单独建 Release（内容已含于 .32 notes） |
| 2026-09-16 晚 | Arena Agent 响应 `.32` 实测失败：快照 `D:\tmp\edsnap-331032-20260916`，新写 `ldb_extract.py` 直接解 WAL，五条诊断链交叉比对（turn_diag `textChars` vs trace 可见文本） | 未改正式目录；产物 `docs/mcp-deepseekpp-capability-exposure.md`、`D:\tmp\fix331033\apply-fix331033.py`、`fix331033-capability-exposure-selftest.js`、干跑树 `D:\tmp\DeepSeekPP-Fix331033-dry`；本文档 §0/§2.7/§3/§5/§7 | **根因实锤（非回归）**：自适应暴露按提示词关键词选工具，`继续` 选不中 `run_command` → `<run_command>` 标签被解析器剥成文本；别名指向已消费句柄 → `mcp_capability_handle_replayed` 无定向纠偏；零工具 `task_complete` 放行。`.33` 五处修复干跑：node --check 4/4、新套件 53/53、全回归 54/54 | 待用户确认后跑 §4 发布链落 `.33`；未升级前把 ShunCode 服务器切 `direct` 模式 |
| 2026-09-16 晚 | 用户确认“全部修复”，Arena Agent 按 §4 发布 **Fix 3.3.10.33**：冻结 `.32` 回退点 → patcher 落正式目录 → 双独立重建比对 → 全回归 → ZIP → GitHub commit + Release | 正式目录 → 1.14.0.38（206 文件）；ZIP `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.33.zip` 13,933,248 B SHA `7A398F4F…B795`；回退点 `D:\tmp\DeepSeekPP-Fix331032-pre331033-20260916`；GitHub `c99119f` + Release `v1.14.0-fix3.3.10.33`（Latest，README 顶部改 .33 Current）；本文档 §0/§3/§5/§7 | 全回归 54/54、双重建 206/206 零差异、重复打补丁 fail-closed。踩坑：正式目录被占用导致 `shutil.rmtree` 失败（已改为先 patch 到临时树再 `cp -r` 覆盖，§6 建议 patcher 勿以正式目录为 dst） | 用户实测 `.33`（§5-0） |
| 2026-09-16 深夜 | 用户报“继续只执行一会再次中断”，Arena Agent 取证（快照 `edsnap-331033-20260916-2319`，`ldb_extract.py` 加 cramjam 全量解表）→ 判定为用户运行中发消息触发 .33107 手动接管（非缺陷）；顺带修 run_command 假失败 + 中断可见；按 §4 发布 **Fix 3.3.10.34**；写用户指南 | 正式目录 → 1.14.0.39；ZIP `.34` 13,946,628 B SHA `ECBCB43D…29FA`；回退点 `D:\tmp\DeepSeekPP-Fix331033-pre331034-20260916`；GitHub `cce959e` + Release `v1.14.0-fix3.3.10.34`（Latest）；仓库/正式目录新增 `USAGE-zh_CN.md`；分析文档 `docs/mcp-deepseekpp-manual-supersede.md`；本文档 §0/§2.8/§3/§5/§7 | 新套件 24/24，全回归 55/55，双重建 208/208 零差异，重复打补丁 fail-closed | 用户按 `USAGE-zh_CN.md` 使用并实测 `.34` |


### 2026-09-17 · read_image v6 候选与维护文档

- 2026-09-17 收口：正式 content.js 已应用 v6，**901444 B**，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`；background 未改。最终隔离报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation-final/report.json`：专项22/22组、旧回归55/55套件、工程检查30/30；应用后实际目标专项再次22/22。5个维护代码文件诊断返回0 error/0 warning，3个Python文件语法通过。原始 .34 `.v5_bak` 与修改前 v5 `.v6_bak` 均已核验。未重载浏览器、未实际上传图片、未发布GitHub/ZIP；端到端识图仍待用户验收。

- 2026-09-17 批次三：隔离验证已通过：实际 helper/Jz **22/22 组**、扩展既有 **55/55 套件**，独立重建一致且树差异仅 content.js；默认只读、重复应用无写入、精确备份/回滚、输入/运行源篡改拒绝、坏语法拒绝、STALE_FILE 与模拟 I/O 失败回滚均通过。报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation/report.json`。追加部署状态自动维护行及其 apply/rollback 断言，避免未来回滚后页首仍称 v6 已部署；正式应用前再验证此维护逻辑。

- 2026-09-17 批次二：首个候选实际 helper + Jz 专项 **22/22 组通过**，Node 语法通过；候选 901444 B，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`。增加 runtime/output 哈希锁、文档读取版本快照保护和独立离线验证器（55 个扩展旧套件 + patcher 篡改/回滚/事务故障测试）；接下来执行这些门。正式 content.js 仍为 v5；未重载/上传。

- 读取用户上传交接文档与工作区读图资料，核实 v5/原始备份/background 哈希。
- 确认首次 toolExecutions 绕过事件捕获、上传回调未 await、全局队列无运行隔离。
- 提交运行隔离的候选 helper、hash-lock patcher 与离线测试；禁用旧 v5 脚本写入入口。
- 本批次不改正式 content.js；不会把离线候选或历史 .34 回归等同于读图成功。
- 后续门槛、隐私边界、测试/回滚见 `docs/mcp-deepseekpp-readimage-v6.md`。

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

### 2026-09-17T15:51+08:00 · .37 → .40 连续四级（诊断 → 修复 → 诊断 → 小修）

- .37（1.14.0.42，14:52 部署）：上传门固定枚举诊断；现场命中 `ctx_sender_tab_session_mismatch`（frame/lifecycle/documentId 全正常）。
- .38（1.14.0.43，15:06 部署）：`DPP_REQUIRE_UPLOAD_CONTEXT_V7` 去掉过期 `sender.url` 会话比较，新增 `dppListenerChatSessionId` 会话锁；离线 20/64，浏览器 15:22/15:27/15:43 三次 upload_ok→refs→ack。background `76df1046…`。
- .39（1.14.0.44，15:41 部署）：main-world 直写 `dpp_mw_bridge_diag_v10`（10 插桩点，仅枚举/布尔/计数）；首轮显示新对话首条消息 tools=24、桥正常，“服务器不可用”为 DeepSeek `generation_err`。
- .40（1.14.0.45，15:51 部署）：`go()` 的 `Y.observe(document.body)` 改为 body 缺失时延后到 DOMContentLoaded；4 组专项 + 22/67 全过。main-world `e63b1676…`。
- 15:5x 发布：用户授权后按 §4 打包（.36 ZIP 布局 + 6 个改动文件 + docs/tools），`SHA256SUMS.txt`，tag `v1.14.0-fix3.3.10.40`，Release Latest。黑曜石同步见下一条；Athena 目录（已 DSPP-free，勿动）。

### 2026-09-17T16:2x+08:00 · 黑曜石同步完成 + 16:00 五次中断取证

- 黑曜石 `dspp/00`–`03` 四篇入口已同步到 .40/1.14.0.45（顶部横幅 + 状态行 + .40 发布回执，.36 回执降为历史）；原文备份 `dspp/_backup-20260917-fix40/`；私有库，不推送。
- 取证快照 `D:/tmp/svg-vision-fix40-20260917-161111`，窗口 15:58–16:08，5 个 agent loop（`265aff17`/`0a410c9c`/`4a13371b`/`bc169888`/`888f44d3`）。
- **五次全部以 `turn_decision=unexecuted_work_limit_331036` 结束（扩展侧安全停止，非网络）**：窗口内 0 条 `xhr_error/abort/timeout`、0 条 `httpOk:false`、0 条 `generation_err`、0 条 `AGENT_LOOP_ERROR`；桥 `send_hook tools=24 / bridge=true`、`run_ready` 每轮正常。
- 直接原因：模型在 `<mcp_t_…_run_command>` 用对前缀名（15 次 `tool_call` 成功执行）后，对读图始终裸写 `<read_image>`（28 次 `unregistered_tool_tag_331033 errorMessage=read_image`，首轮另有 4 次裸 `<run_command>`）。裸标签不在注册表（注册名是 `mcp_t_9a351af5_…_read_image`），被 .33 检测器判为未注册→`visual_preflight_331036` 纠偏；同一 step 内 3 次 tool-intent 纠偏后触发 `DPP_TOOL_INTENT_NUDGE_MAX_331021` → 停止并输出"DeepSeek 连续 3 次明确表示要调用工具，但仍未输出可执行 tool call"。
- 助推因素：(a) .36 `DPP_VISUAL_RULES_331036` / `DPP_VISUAL_RETRY_331036` 提示词多次以裸名 `read_image` 要求调用，未给真实标签名；(b) `DPP_UNREGISTERED_TAG_STEERING_331033` 对裸 ShunCode 标签一律指向 `mcp_discover`，而此处工具明明已在目录中（应改为提示精确前缀标签），提示自相矛盾，模型反复空转。
- 本窗口无 read_image v7 / upload gate 新行——因为 read_image 一次都没真正执行到，.38 上传链路未被触及；不是回归。
- 建议 .41（未实施、待用户裁定）：① 检测器命中裸 ShunCode 名且注册表中存在 `*_${base}` 前缀工具时，纠偏文案改为"请使用精确标签 `<mcp_t_…_base>`"，不再引导 discover；② 视觉规则/重试文案带上运行时真实的 read_image 注册名；③ 可选：解析层把裸 ShunCode 标签别名到唯一匹配的前缀工具（行为变更，需单独门禁）。不涉及授权检查。

### 2026-09-17T16:30+08:00 · .41 任务书与接手入口

- 新增 `docs/mcp-deepseekpp-bare-tool-tag-fix41.md`：16:00 五次中断的取证表、根因（裸 `<read_image>` 标签 × 自相矛盾提示词 × 3 次 tool-intent 纠偏上限）、.41 方案 A/B/C、实施与验收流程。
- 顶部新增 16:30 接手入口，列出下一个智能体的阅读顺序与硬约束。未改运行代码，未发布。

### 2026-09-17T17:0x+08:00 · .41 裸工具标签修复（已部署，待浏览器验收）

- 实施 `docs/mcp-deepseekpp-bare-tool-tag-fix41.md` 的 A/B/C（D 未做）：纠偏文案给出精确注册标签、视觉规则/重试文案注入真实 read_image 名、`unregistered_tool_tag_331033` 新增 `resolution` 三值枚举。
- 链式 builder `tools/apply-fix331041.py`（先跑 .40 builder 再打 .41 补丁，中间树用后即删）+ 哈希锁 `fix331041-source-sha256.json`；基线仍为干净 `.36` 树。
- 1.14.0.46 / Fix 3.3.10.41 已写入 live（216 文件）；只改 content.js；回退点 `D:/tmp/DeepSeekPP-Fix331040-pre331041-20260917`（215 文件）。
- 验收：专项 34/34、validator passed:true（31/69/56）、v8 48/48、live 56/56、三类篡改 fail-closed、独立重建 228/228 零差异。
- 偏离任务书两处（已验证、已记入 §6.2）：① 注册名匹配不写死 serverId 段数；② 四处改点必须内联自包含（v8 套件单独 eval）。
- 经用户授权修改已发布套件 `tools/dspp-visual-workflow-v8-selftest.js` 第 84 行字面量断言以适配新参数，断言意图不变。
- 未打 ZIP、未打 tag、未发 Release；黑曜石 dspp 未同步。浏览器未验收前不声称故障已修复。

### 2026-09-17T19:5x+08:00 · .41 浏览器验收通过

- 快照 `D:/tmp/edsnap-331041-verify-20260917`（19:56 取，`001036.log` 1,979,281 B）；`dpp_agent_turn_diag_331021` seq 11736，窗口 16:04:26–19:54:11。
- 19:53 loop `924059bb`：`status=complete`、5 步 5 工具，链路 read_image(首次 `mcp_tool_result_error`) → run_command → **read_image ok=True** → run_command → `task_complete`。
- **关键证据**：`unregistered_tool_tag_331033` 在 17:00 后 **零条**（10 条全为 16:04–16:07 的 .40 旧数据）——模型直接用了注册全名，纠偏路径未被触发；A/B 达到目的。`unexecuted_work_limit_331036` 同期 0 次（.40 时五次全中）。
- 诚实边界：改点 C 的 `resolution` 枚举**现场未观测到**（模型未再写裸标签，无触发机会），仅有离线自测覆盖；本次为单次验收，不等于全面回归；首次 read_image 报 `mcp_tool_result_error` 已记为观察项。

### 2026-09-17T20:1x+08:00 · .41 已发布（用户授权）

- commit `2dec8a8` 推送 `origin/main`；tag `v1.14.0-fix3.3.10.41`；GitHub Release 已为 **Latest**。
- 附件 ZIP 9,136,857 B / 140 条目，SHA-256 `efabab74bc7e29ee41a14f65367f31b06d1ae94c9f78dd2583dd8f0005f71a11`；回下载字节 = 本地产物 = SHA256SUMS 声明值，三者一致。
- 从 clone 独立重建：哈希锁 3/3 通过，7 个运行时文件与 live 逐字节一致 —— 第三方可复现。
- 修正 `.gitattributes`：哈希锁 JSON 锁定 `eol=lf`，否则 clone 后 CRLF 转换会让下游 builder 自检失败。
- 待办：黑曜石 dspp 同步 .41；`resolution` 枚举仍待现场观测；首次 read_image `mcp_tool_result_error` 为观察项。

### 2026-09-17T20:5x+08:00 · .41 收尾（黑曜石同步 / 备份清理 / 镜像刷新）

- 黑曜石 `C:/Users/29066/Documents/GitHub/ALTRKIE-/dspp/00`–`03` 四篇加 .41 顶部横幅、状态行改 .41/1.14.0.46、新增 .41 发布回执（.40 回执降为历史）；原文备份 `dspp/_backup-20260917-fix41/`。私有库，不推送。
- 仓库工作树未跟踪备份 `交接文档.md.bak-20260917-pre41` / `-prefill41` / `docs/…fix41.md.bak-20260917-prefill` 移入 `local/_doc_backups_20260917/`（`.gitignore` 已含 `/local/`），`git status` 恢复干净。
- 桌面镜像副本由仓库真源覆盖（此前为 .34 旧版）。§0 TL;DR 五行更新到 .41。
- 未改运行代码、未打包、未发版。诚实边界：本条为文档/笔记维护，不新增任何关于 .41 行为的证据。

### 2026-09-17T21:0x+08:00 · .41 部署后裸标签空转复现（取证，未改代码）

- 20:53–20:56 同一会话三个 loop 全部 `unexecuted_work_limit_331036`（裸 `run_command`×4、`read_image`×4×2），纠偏路径在跑但模型不改；网络正常。详见 `docs/mcp-deepseekpp-bare-tool-tag-recurrence-20260917.md`。
- 发现 .41 改点 C 缺陷：`resolution` 字段被 turn_diag 白名单丢弃，现场永不落盘。
- 结论：A/B 提示词路线不够，建议 .42 做方案 D（唯一匹配时别名直执）+ 修 C；待用户裁定。

### 2026-09-17T21:4x+08:00 · .42 工具暴露漂移修复（已部署 live，待验收）

- 根因：见顶部 21:4x 入口与 `docs/mcp-deepseekpp-exposure-drift-fix42.md` §1–2。`USAGE-zh_CN.md` §2.2 原“只启用 ShunCode 不会触发降级”一句为错误陈述，已更正。
- 改动：`fix3-policy.js` 两处字面量（触发线 48000；仅未显式设置模式的服务器可被降级）、`background.js` 三处（默认/上限 8 槽 24 KB；`read_image` floor 1000）、`content.js` 一处（turn_diag 白名单 `resolution`）；三份已发布套件的字面量断言适配；新增 `dspp-exposure-drift-v42-selftest.js` 21/21。
- 验证：validator passed:true（22/69/57）；篡改基线/篡改源/重复打补丁 fail-closed；独立重建两次一致；live 57/57；live 与 .41 回退点相比仅 6 运行时文件 + 版本门套件不同。
- 部署插曲：候选树含仓库布局的 docs/tools 额外文件，首次覆盖后按 .41 回退点恢复布局，只替换 7 个运行时文件 + 套件，最终 217 文件。
- 未验收、发布状态见下一条。

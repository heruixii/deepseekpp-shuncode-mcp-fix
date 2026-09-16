# DeepSeek++ 扩展修复项目 · 交接文档

> **这份文档是项目的唯一交接入口。每次对项目做任何改动（修复、发版、验证、结论更新）后，都必须更新本文档**（改对应章节 + 在文末「更新记录」追加一条），保证任何人接手都能从本文档直接进入状态。
>
> - 创建时间：2026-09-16
> - 创建方：Arena Agent（经 ShunCode Bridge MCP 连接本机）
> - 信息来源：ChatGPT 分享对话《分析页面崩溃原因》(https://chatgpt.com/share/6aaa2f87-4e60-83ee-86c1-63215ea6b70d) + 本机工作区 `D:\learn\Athena计划`

---

## 0. 一页速览（TL;DR）

| 项目 | 状态 |
|---|---|
| 在做什么 | 修复 **DeepSeek++ 浏览器扩展**在自动化执行任务时导致 **DeepSeek 网页崩溃 / "服务器暂不可用" / 任务中断** 的系列问题 |
| 当前正式版 | **`1.14.0.35 / DeepSeek++ ShunCode MCP Fix 3.3.10.30`** |
| 正式目录 | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`（Edge 解压加载） |
| 最新成就 | **网页频繁崩溃根因实锤并修复**：CDP 现场抓获——扩展恢复注入与 DeepSeek React reconciler 互撞，`insertBefore` NotFoundError → app 错误边界「页面崩溃」屏；`.30` 装 MAIN-world DOM 保险丝，只吞 NotFoundError 并就地恢复 |
| 当前阶段 | **Fix 3.3.10.30 已发布并经用户实测通过**（2026-09-16）：根因=扩展注入互撞（§2.4），发布链绿灯 + 重载后硬刷新崩溃会话确认修复。代码与本文档已同步 GitHub `heruixii/deepseekpp-shuncode-mcp-fix` |
| 下一步 | ①`.29` 验收闭环（稳定化计划第 27 节收尾 + `.30` 补第 28 节）；②GPU 141 A/B 机器级观察项（§5）；③候选 `.31`：剩余整值重写通道分片化 |
| 如果复现 | 对 Agent 说 **"查看新日志"**；自查项：console 有无 `NotFoundError` 刷屏、`localStorage["dpp_dom_fence_diag_331030"]` 计数是否在涨（在涨=保险丝正在替你挡互撞） |
| 当前回退点 | `D:\tmp\DeepSeekPP-Fix331029-pre331030-20260916`（.29 冻结版） |

---

## 1. 项目概况

### 1.1 生态组成

- **Athena 计划**（ShunCode 工作区 `D:\learn\Athena计划`）：桌面 AI 助手主项目（`main.py`、Live2D、GPT-SoVITS TTS、wxauto 微信自动化等目录）。MCP Bridge 默认工作区即此目录。
- **DeepSeek++ 扩展（deepseek_pp）**：Edge 浏览器解压扩展，增强 DeepSeek 网页版——自动化任务队列、网页 Agent 连续执行、经 **MCP capability / mcp_invoke** 调用本机 ShunCode 工具、提示词/记忆注入、usage 统计、trace 诊断等。这是本修复工程的主体。
- **ShunCode Bridge**：把 IDE/Agent 能力桥给网页 Agent，扩展崩溃问题长期集中在**网页 Agent / 恢复上下文**链路，而非 Bridge 本身。

### 1.2 关键路径

| 用途 | 路径 |
|---|---|
| 正式扩展目录（Edge 加载此目录） | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` |
| 正式 ZIP（当前 .29） | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.29.zip` |
| 当前 ZIP SHA-256 | `C83459E9EE10CD1FD1D8C0B19307026A7CA4BAF79A85176A9A98222C629A8D7A` |
| 回退点（每次发版前冻结上一版） | `D:\tmp\DeepSeekPP-Fix3310XX-pre3310YY-20260916` |
| 工作区（Athena） | `D:\learn\Athena计划` |
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

### 2.3 关键区分

- 用户最初怀疑"记忆注入导致崩溃"——查实当时真实设置是 `memoryEnabled=false`、`systemPromptEnabled=true`，**普通记忆注入早已关闭**；罪魁是 **system/tool prompt 每步全量注入 + 累计工具结果反复注入**导致的上下文膨胀。
- 注意：**旧的 ~196K token 对话不会因升级插件而瘦身**，测试必须**开全新对话**，否则污染结果。

---

## 3. 修复历程（Fix 3.3.10.11 → 3.3.10.30）

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

> 所有版本的完整根因、证据、哈希、回归记录都写在扩展目录内的**稳定化计划**（已到第 27 节）与 `FIX3-TEST-REPORT.md`。

---

## 4. 发布工程规范（本项目的工作方式，务必遵守）

1. **hash-lock patcher**：每版生成锁定上一版六个核心 SHA 的 `.N → .N+1` patcher；干净输入精确升级，篡改输入 **fail-closed**，绝不允许半升级。
2. **独立重建验收**：builder 必须从冻结的上一版**独立重建**新版，与正式目录**整树逐字节比对**（missing=0 / extra=0 / diff=0）才算通过。
3. **发版前冻结回退点**：上一版完整目录冻结到 `D:\tmp\DeepSeekPP-…-pre…-日期`，正式 health 失败就回退。
4. **稳定化计划**：每版追加一节（根因、证据、机制、验证、最终哈希）。
5. **诚实边界**：不夸大结论（例：.29 明确写了"降低写压力 ≠ 已证明修复浏览器崩溃"）。
6. **测试规矩**：`edge://extensions` 重新加载解压扩展 + **彻底关闭旧 DeepSeek 标签页后开新标签页**（不能只"新建聊天"，旧标签页不重载仍跑旧脚本）；不用超长旧对话测试；验收以**任务最终真正完成**为准，不能拿"中间执行了几次工具"当成功。

---

## 5. 下一步工作（接手从这里开始）

1. **【先做】.30 现场验证**：`edge://extensions` 重新加载扩展 → 彻底关闭旧 DeepSeek 标签页后开新页 → 硬刷新此前必崩的会话 `c0ba574e`。预期：不再出现「页面崩溃」屏；console 可能出现被保险丝拦下的 NotFoundError（不致命），`localStorage["dpp_dom_fence_diag_331030"]` 计数如 >0 属正常（保险丝在工作）。
2. **【降为观察项】GPU 141 A/B**（机器级，独立于网页崩溃问题；每步后连续跑 2~3 个同等级任务看 WER 是否还新增 141）：
   - **A. 退净串流/安卓模拟器**：完全退出 GameViewer（UU 远程）与 MuMu 模拟器及其后台服务 → 重测。
   - **B. Edge 关硬件加速**：`edge://settings/system` 关闭"使用硬件加速(如可用)" → 重启 Edge 重测。
   - **C. 固定单 GPU**：Windows 设置 → 系统 → 显示 → 图形 → 把 msedge.exe 固定为"节能(Intel)"或"高性能(NVIDIA)"其一 → 重测。
   - 任一步崩溃消失 → 根因收敛；都不消失 → D: 更新 Intel UHD 驱动（2024-01 版本偏旧）/ WinDbg 分析 `C:\Windows\LiveKernelReports` 新 dump（P2/P3 定位挂死模块）。
3. `.30` 验证通过后：回 `.29` 验收闭环（稳定化计划第 27 节收尾），并把 `.30` 补进第 28 节。
4. 排期候选 **`.31`**：剩余整值重写通道分片化（turn_diag / tool_history / inline_agent_traces / tool_execution_blocks / tool_shape_diag，见 §2.4 尾）——按 §4 全套发布链执行。
5. 长期观察项：旧 v1 usage 536 KB 数据的去留（目前策略是只读保留、不迁移）。

---

## 6. 排查定位技巧（沉淀的经验）

- **Edge 扩展 LevelDB 做只读快照**再分析（注意 Git Bash 的 `/c/...` 路径 Windows Python 不认，要用 `C:\...`）。
- 诊断 keys：`deepseek_pp_usage_turns_v1`（旧大键）/ `v2_meta`、`v2_day_*`（新分片）、`dpp_web_response_diag_331015`（响应诊断）、`agent_exception_331023 + stackHead`（异常+栈头）、Agent trace / tool history / turn diagnostics。
- 服务端 token 轨迹看 usage 记录 `totalTokens` 增长；每步涨 4k~7k 即注入放大。
- 崩溃证据链：Edge Crashpad 新 dump、Windows WER（`LiveKernelEvent 141` 要看引用的 dmp 是否为本次新文件、Report ID 是否重复）。
- **WER 直接查事件日志更快**（Application 日志无需管理员）：`Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddHours(-26)} | ? {$_.Message -match 'LiveKernel'}`；同一 P2/P3 = 同一挂起引擎。ReportQueue 文件夹与 `C:\Windows\LiveKernelReports` 需管理员。
- **LevelDB WAL 解析器已沉淀**：`D:\tmp\analyze_leveldb.py`（解析 WriteBatch，统计每 key 写入字节/次数）；快照目录 `D:\tmp\edsnap-331029-repro-20260916\`；key 值导出 `D:\tmp\keysnap_*.txt`。取快照只需 cp `.log/.ldb/LOG/MANIFEST`，不必锁库。
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

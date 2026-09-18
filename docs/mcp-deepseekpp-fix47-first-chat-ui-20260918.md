# Fix 3.3.10.47：新会话生成失败、标题污染与任务 UI

2026-09-18，用户授权修复并优化 DeepSeek 网页显示。本轮已部署本机 .47 / 1.14.0.52；浏览器重载后的现场验收待完成。

## 1. 新日志：不是 .46 缓存修复回归

私有热快照：D:/tmp/edsnap-fix46-firstchat-20260918-105343；Edge Default 扩展 LevelDB 和 Local Storage/leveldb 复制后离线解析，跳过 LOCK。热快照不等于停机一致性数据库备份；未修改浏览器日志、设置或历史标题。

| 会话前缀 | 响应时间 | descriptorCount | raw / augmented 字符 | 终态 |
|---|---|---|---|---|
| 60df2079 | 10:40:21.127 | 24 | 881 / 37452 | generation_err / INCOMPLETE |
| dffd10b9 | 10:40:34.873 | 24 | 881 / 37452 | generation_err / INCOMPLETE |
| dffd10b9 | 10:40:42.392 | 24 | 206 / 20335 | compact 后仍 generation_err |
| c33bfec2 | 10:41:03.748 | 24 | 881 / 37452 | FINISHED，后续多步工具执行 |
| c33bfec2 | 10:50:13.404 | 24 | 216 / 36138 | FINISHED，后续再次执行工具 |

三次首次请求的 content_auth1_done 与 mw_augment_result 均存在，augmented=true，增强约 41–49ms。失败与成功首请求同样 37452 字符，不能仅凭体积推断“首轮必然因大提示词失败”。明确证据是 DeepSeek HTTP 200 SSE 中的 finish_reason=generation_err；不是 MCP 断连，也不是 .45 的 descriptorCount=0。

**诚实边界：**用户描述第一轮/第二轮行为；日志显示两个新会话失败、第三个会话成功。尚无足够证据证明确定性的冷启动竞态，不能声称控制了 DeepSeek 服务端或消除了其所有生成错误。

## 2. 已确认的扩展侧缺陷

### 2.1 标题污染和记忆关闭不一致

设置 deepseek_pp_prompt_injection_settings.memoryEnabled=false、systemPromptEnabled=true。但 content.js 的 vo() 仍无条件采用 prompt.systemThinking/systemChat，开头为“你具有长期记忆能力。已有记忆…”，而且包含自动 memory_save 指令。真正用户任务放在后面。用户观察到失败会话被命名为该前缀；代码证明污染文本确实在请求前部，但本轮未获取 DeepSeek 标题生成内部算法。

.47 在记忆关闭时改为中性的工具执行说明，不再声称已有长期记忆、不再要求自动保存；系统提示开启时，在请求最前面放真实可见用户任务的至多 240 字符单行前缀。原始完整任务、技能可见提示元数据、工具名称及参数 schema 保留。记忆开启时保留既有记忆上下文，systemPromptEnabled=false 时不新增前缀。旧云端标题不自动覆盖，修复面向后续请求和新标题。

### 2.2 恢复窗口与 fetch EOF 关联

旧 one-shot compact recovery 只有 12 秒，手动等待后续接容易过期。扩展到 10 分钟，仍严格要求同会话且 parentMessageId 等于失败 assistantMessageId；不跨会话继承，成功清理、消费一次后移除、到期失效。保留 .26 的 compact 再失败后 passthrough 策略，不增加自动网络重放。

另：MAIN-world to(e,t) 的 ReadableStream.pull 内 let {done:t} 遮蔽请求元数据；EOF 的 DPP_TRACK_GENERATION_RESULT_331020(t,a) 实际收到布尔值，fetch 路径无法正确登记恢复。新实现捕获独立 DPPRequestMeta331047 并在 EOF 使用。**本次现场是 XHR，因此这是复核发现并行为复现的旁路缺陷，不当作三个 XHR 失败的直接原因。**

### 2.3 compact schema 的有损裁剪

原 helper 有深度 4、24 个 properties、6 个分支上限，并漏保留 $ref/$defs、allOf/not、pattern/minLength 等约束。新 helper 仅去掉说明性 description/title/examples/$comment；保留全部属性、分支、引用、约束、布尔 schema。properties/$defs 等命名空间中的 description/title 是合法属性名，不能删除；const/enum/default 中的业务数据保持完整。

### 2.4 Agent 错误分类和 UI 丢失错误详情

HR() 遇到已明确 generation_err 的流，原先仍可进入工具意图纠偏。新代码保留已流出的内容，但抛明确、不可自动重试的生成中断错误，不把服务端失败消耗成多轮“请调用工具”的 nudge。空流限流逻辑保留，不新增隐式重放请求。

RX() 本来通过 labelOverride 传入真实失败原因，但 QB() 清空 status-detail，compact text 又只显示“发送继续恢复”，信息被吞掉。新面板展示真实 labelOverride（最多 600 字符、textContent，不作为 HTML），并分列成功/运行中/失败/中断数量。

## 3. 网页显示优化

- 简洁的任务卡片：状态、当前动作、工具结果统计、耗时、停止及详情按钮。
- 移除看似任务完成百分比的进度条；不将安全步数预算冒充任务进度。
- 详情默认收起，冗长思考与步骤正文仍默认隐藏；最终结果单独展示。
- 失败原因直接可见，不再仅显示通用“继续恢复”。
- 手动请求 generation_err / rate_limit_reached 会显示可关闭的明确提示；成功回复或导航清理提示。
- 提示仅追加到 document.body 的扩展自有 aside；不移动或替换 DeepSeek React 管理的消息节点。提示经会话 ID 校验，防止旧会话迟到结果污染当前页。
- 响应式宽度、深色配色、aria-live、真实按钮；新增界面行为由 DOM 桩测试覆盖，未声称已在真实 Edge 完成视觉截图验收。

## 4. 实施与验证

- builder：tools/apply-fix331047.py，链式 .36 → … → .46 → .47；源锁 tools/fix331047-source-sha256.json。
- validator：tools/validate-fix331047.py，11 项完整性/范围检查、73 个验证进程、63 套自测全部通过；独立重建 235 个文件字节一致。
- 新专项 tools/dspp-startup-ui-v47-selftest.js：28/28，包括提示前缀、记忆开关、完整 schema、30 秒延迟恢复、会话隔离/到期、实际 fetch EOF、Agent generation_err 单次停止、提示生命周期、可见错误文本。
- 旧诊断测试保留：终端日志持久化断言原样通过。v47 MAIN-world 诊断派生套件先逐项逆转三处精确批准变更，再执行原 .39 全量逆补丁比较和诊断行为检查，没有简单删除完整性断言。
- 源篡改、基线篡改、重复输出三项 fail-closed 通过。
- background.js、fix3-policy.js 与 .46 完全相同；授权函数、runtime allowlist、manifest 非版本字段保持一致。
- 本机部署：D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3，仅更新经旧版本字节核验的 36 个变更文件；manifest 最后替换。
- 部署前完整备份：D:/tmp/DeepSeekPP-Fix331046-pre331047-20260918，逐文件校验后才写入。部署后 live 63/63 自测通过。
- 验证与部署回执分别在 D:/tmp/deepseekpp-fix331047-validation-final-20260918/report.json、D:/tmp/deepseekpp-fix331047-safety-20260918/deployment.json；机器报告私有副本在 local/fix331047/，不公开原始日志或快照。
- 未改浏览器设置、未重载运行中的扩展或关闭标签、未调用 DeepSeek 实际生成接口验收、未修改历史标题、未创建 ZIP/tag、未提交推送或发布 GitHub。

## 5. 浏览器验收与剩余边界

1. 重载扩展，确认 1.14.0.52；关掉旧 DeepSeek 标签，打开新页面。
2. 第一个新会话先做简短的只读 MCP 任务，检查标题与任务相关、真实工具执行成功、任务卡片统计和详情按钮正常。
3. 若仍出现服务器不可用，记录时间；核对 finish_reason、HTTP 状态和 descriptorCount，而非再次盲目归因于工具断连。
4. 遇到 generation_err 时待 Agent 停止后，等待超过 12 秒但小于 10 分钟，再在同会话发送“继续”；验证匹配父回复时 recoveryMode=compact，失败原因可见。连续后端失败仍可能触发原有 passthrough；本轮不宣称能保证第三方服务成功。
5. 新旧会话切换，确认失败提示不串会话；新标题不会再以注入的“你具有长期记忆…”作为请求首部。已有污染标题需用户自行重命名，本轮不覆盖用户历史标题。
6. .46 的 MCP 目录恢复已有本次现场证据；.47 的首轮、标题和实际 UI 表现须以升级后浏览器日志/页面验收为准。

发布说明：docs/RELEASE-Fix3.3.10.47.md。前版：docs/RELEASE-Fix3.3.10.46.md。

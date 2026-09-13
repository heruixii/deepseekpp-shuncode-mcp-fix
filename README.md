# DeepSeek++ ShunCode MCP Fix 3.3

这是基于 **DeepSeek++ 1.14.0** 的稳定性优化版本，重点改善 DeepSeek 网页端通过 MCP 长时间调用 **ShunCode** 时的工具调用可靠性、连续执行能力和异常恢复行为。

> 本仓库不是 DeepSeek++ 官方分支，也不隶属于 DeepSeek 官方团队。它是在原项目基础上的个人优化与兼容性修复版本。

## 原项目与原作者

原项目：**DeepSeek++**  
原仓库：[`zhu1090093659/deepseek-pp`](https://github.com/zhu1090093659/deepseek-pp)  
原项目维护者 / GitHub 作者：**zhu1090093659**  
Chrome Web Store 发布者：**chunlinzhu666**  
原项目许可证：**Apache License 2.0**

DeepSeek++ 是一个面向 DeepSeek 网页版的开源浏览器扩展，提供 MCP、记忆、Skills、自动化、联网搜索、浏览器控制、对话导出等 Agent 工作流能力。

本仓库保留原项目归属与许可证。所有基础功能、UI、主体代码和原始设计均来自上游 DeepSeek++；本仓库主要集中于 ShunCode MCP 场景下的可靠性修复与执行策略优化。

## 本版本做了什么

### 1. MCP 工具调用解析增强

增强 DeepSeek 输出到工具调用之间的容错处理，减少因为模型生成格式轻微异常导致的调用失败，包括：

- 工具命名空间和后缀识别
- wrapper 解包
- `run_command` 参数归一化
- `apply_patch` 参数别名
- Windows 路径和反斜杠转义修复
- 非法 JSON escape 修复
- 嵌套引号、字面换行、控制字符处理
- 尾随逗号和 fenced JSON 修复
- JSON 前后夹杂说明文字时的提取
- `run_command` / `apply_patch` raw body 支持
- 保守的 EOF 自动闭合
- schema-aware 参数别名与类型转换

目标不是让解析器“猜测一切”，而是在不使用 `eval`、不放宽安全边界的前提下，提高模型工具调用的成功率。

### 2. ShunCode MCP 长任务连续执行

修复模型在长任务中执行几步后，输出类似“先测试”“下一步检查”“还需要验证”却提前结束的问题。

现在加入：

- 中间步骤语义识别
- 最多 8 次连续纠偏 nudge
- 工具真正取得进展后才重置 nudge 计数
- “继续 / 接着 / continue / go on”等短指令自动获得长任务步数预算
- 普通任务、项目任务、明确要求执行到完成的任务采用不同 step budget
- 连续重复相同工具和参数时进行 no-progress 阻断

对于“继续直到完成”一类任务，最大执行步数提升到 **36**，硬上限仍保留，避免无限循环。

### 3. Completion Gate：修改后必须验证

Fix 3.1 增加了完成门槛：

如果模型刚刚进行了文件修改、命令写入、安装、提交等操作，但之后还没有成功的读取、诊断或测试验证，就不能直接把任务标记为完成。

系统会区分：

- `mutation`：修改、写入、patch、删除、移动、安装、提交等
- `verification`：读取、搜索、诊断、状态检查、测试等
- `neutral`：无法安全归类的命令

这样可以减少“工具返回成功，所以模型直接宣布完成，但实际上没有检查结果”的情况。

### 4. 副作用命令的模糊结果保护

对于 `run_command`、`apply_patch` 等可能产生副作用的调用，如果网络在执行过程中断开，外部状态可能已经发生变化。

本版本会把这类情况标记为：

```text
externalOutcome = ambiguous
retrySafe = false
```

因此不会自动盲目重放同一条副作用命令，而是要求先检查当前状态再决定下一步。

这避免了重复写文件、重复提交、重复安装或重复执行命令。

### 5. Capability / Adaptive 修复

Fix 3.2 重点修复了 MCP capability 工作流：

- 保留 capability handle 的 **single-use / 防重放** 设计
- `mcp_discover` 即使进入旧结果 windowing，也仍然保留最小 `{capability, name, expiresAt}`
- 新 discover 结果压缩为最小 catalog，不再因为上下文压缩丢失 handle
- `handle_replayed / expired / invalid` 明确指导重新 discover
- 修复 Adaptive 路由中的中文关键词乱码
- “文件 / 目录 / 读取 / 搜索 / 修改 / 写入 / 命令 / 执行 / 运行 / 测试 / 仓库 / 提交”等中文任务可以正确参与工具排名
- “用命令写入文件”这类意图会优先提高 `run_command` 排名

实际使用中，ShunCode 当前只有约 12 个工具，因此本仓库更推荐 **Direct exposure**，直接暴露已授权工具，避免不必要的 `discover -> invoke` 中转。

### 6. 自适应工具路由

在 Adaptive 模式下，根据任务意图动态提高对应工具优先级，例如：

- 文件读取 → `read_files / search_files / find_files`
- 文件修改 → `apply_patch`
- 命令、构建、测试 → `run_command`
- Git / GitHub → `run_command` 等相关工具

同时会参考最近成功使用过的工具，并带时间衰减，减少模型反复在不合适的工具之间跳转。

### 7. 工具结果上下文压缩

长时间 Agent 任务中，完整工具输出会快速占满上下文。

本版本只压缩“发送给模型的上下文副本”，不会修改：

- 原始 MCP 返回结果
- 工具历史记录
- ShunCode 本身的输出

不同工具使用不同模型上下文预算，例如状态类、读取类、命令类分别采用不同大小上限。

### 8. 长命令交给 ShunCode `script_bridge`

Windows 下很长的 PowerShell / shell 命令不在扩展里重复实现另一套临时脚本机制。

本版本直接复用 ShunCode 自带的 `script_bridge`，减少双层转义、双层状态机和额外耦合。

### 9. 低耦合、可回滚补丁结构

优化按独立 overlay 分层：

- `apply-fix3.py`
- `apply-fix31.py`
- `apply-fix32.py`

构建顺序为：

```text
Fix 2 source
  -> Fix 3
  -> Fix 3.1
  -> Fix 3.2
  -> Fix 3.3
  -> health check
  -> release
```

每个补丁都采用 fail-closed 设计：如果目标 marker 不唯一或目标版本不兼容，构建直接失败，不进行模糊替换，也不留下半成品。

### 10. Fix 3.3：DeepSeek 流兼容与本地执行安全

Fix 3.3 针对 2026-09 DeepSeek 网页更新后暴露出的新稳定性问题做窄修复：

- **DeepSeek stream completion 兼容**：递归识别嵌套 `response/status=FINISHED` 与既有 `quasi_status=FINISHED`，但不会把普通正文里的 `FINISHED` 当成完成。
- **安全 EOF 恢复**：只有在没有正文、没有 reasoning、没有 response/request message id 的空 EOF 才允许额外重试一次；已经出现部分输出时绝不自动拼接或重试。
- **隐私受限的 stream 诊断**：异常只记录最近少量 SSE 结构字段（event / p / o / status），不保存正文内容。
- **UTF-8 数据完整性保护**：Windows PowerShell 5.1 下，阻止“裸 `Get-Content -Raw` 读取 UTF-8 无 BOM 文件后再写回”的危险组合，避免中文被 ANSI/GBK 误解码后永久写坏。
- **公共工具 preflight**：第一轮工具调用和 Agent 后续调用都会检查 schema 必填参数；空 `{}` 不再先发往 MCP。
- **workspace 范围恢复提示**：ShunCode 文件工具遇到 `FILE_NOT_FOUND` 时明确提示当前 workspace 边界，外部绝对路径改走 `run_command`，减少无意义重试。
- **PTY 空输出恢复**：仅对已分类为只读/验证的 `run_command`，当 PTY 明确 `exit_code=0` 且 `total_output_bytes=0` 时用 `execution=direct` 补做一次读取；修改/写入/提交类命令绝不因此重放。

这些修复不改变 capability 单次使用规则、不修改 MCP 授权语义、不复制 ShunCode `script_bridge`，也不把“流 EOF”粗暴视为成功。

## 当前版本

```text
DeepSeek++ 1.14.0 ShunCode MCP Fix 3.3
```

GitHub Release：[`v1.14.0-fix3.3`](https://github.com/heruixii/deepseekpp-shuncode-mcp-fix/releases/tag/v1.14.0-fix3.3)

发布 ZIP：

```text
DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.zip
```

SHA-256：

```text
See GitHub Release asset digest / local Get-FileHash output
```

## 推荐 ShunCode MCP 配置

对于当前这套 ShunCode MCP：

```text
Transport: Streamable HTTP
Execution Enabled: On
Execution Mode: Auto
Prompt Exposure / Exposure Mode: Direct
Connect Timeout: 10000
Request Timeout: 120000
Discovery Timeout: 20000
Max Result Bytes: 128000
Max Tool Count: 32
```

由于 ShunCode 工具数量较少，推荐使用 **Direct**。Adaptive 仍然可用，但没有必要为了十几个工具额外引入 capability 中转。

## 安装

1. 下载最新 Release ZIP。
2. 解压到固定目录。
3. 打开 Edge / Chrome 的扩展管理页面。
4. 开启开发人员模式。
5. 选择“加载解压缩的扩展”。
6. 选择解压后的扩展目录。
7. 打开 DeepSeek 网页并配置 MCP。

如果更新的是同一路径下的 unpacked 扩展，只需要在扩展管理页点击“重新加载”，然后对 DeepSeek 页面执行强制刷新即可。

## 验证情况

最终 Fix 3.3 已经过以下验证：

- MCP parser / schema：**17/17 PASS**
- Fix 3 policy：**19/19 PASS**
- DeepSeek 网页执行策略：**21/21 PASS**
- continuation helpers：**11/11 PASS**
- continuation flow：**6/6 PASS**
- Fix 3.1 Agent / completion / retry：**31/31 PASS**
- Fix 3.2 capability / adaptive：**17/17 PASS**
- Fix 3.3 已知问题修复：**46/46 PASS**
- Fix 3.3 真实 SSE parser 集成：**8/8 PASS**
- 全部 JS 语法检查：**PASS**
- Python overlay 编译：**PASS**
- fail-closed 验证：**PASS**
- 从干净基线重建后文件哈希完全一致：**PASS**
- 隔离 Edge unpacked 扩展加载 / Service Worker：**PASS**

更详细的测试记录见 [`FIX3-TEST-REPORT.md`](./FIX3-TEST-REPORT.md)。

## 与上游的关系

本仓库的目标不是取代 DeepSeek++，而是针对 **DeepSeek Web + ShunCode MCP** 的特定工作流做稳定性增强。

如果你不使用 ShunCode，或者不需要长时间、多步、文件/命令密集型 Agent 工作流，优先使用上游官方版本：

https://github.com/zhu1090093659/deepseek-pp

如果你使用的是：

```text
DeepSeek Web
+ DeepSeek++
+ Streamable HTTP MCP
+ ShunCode
+ 长时间连续 Agent 任务
```

那么这个版本主要解决的就是这条链路里的解析、路由、连续执行、结果压缩、异常恢复和完成验证问题。

## 致谢

感谢 DeepSeek++ 原作者 / 维护者 **zhu1090093659** 提供开源项目与完整的浏览器 Agent 基础能力。

感谢原项目 Chrome Web Store 发布者 **chunlinzhu666**。

本仓库中的 DeepSeek++ 原始代码及其衍生部分遵循上游 **Apache License 2.0**。本仓库的优化代码在不改变上游版权归属的前提下随项目一并发布。

## License

本仓库基于采用 **Apache License 2.0** 的 DeepSeek++ 项目修改。

详见 [`LICENSE`](./LICENSE)。

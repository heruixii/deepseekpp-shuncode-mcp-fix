# ShunCode 覆盖安装后的 read_image 检查与恢复

更新：2026-09-17 · 配套 DeepSeekPP Fix 3.3.10.35 / 扩展版本 1.14.0.40。

## 两段链路，分别维护

1. **ShunCode 原生 MCP 端**：`read_image` 成功结果需要 `content` 中的 `{type:"image",data:<base64>,mimeType:...}`。`structuredContent` 仅携带 metadata，避免把 base64 再塞入文本上下文。
2. **DeepSeekPP 浏览器端**：捕获本轮读图结果，经后台实际上传服务获取文件 ID，再注入下一次 Web completion 的文件引用。只有文字说“已读取图片”不等于已看见图片。

ShunCode 覆盖安装可能替换第 1 段的 `runtime/mcp-server.js` 和 `dist/extension.js`。本仓库发布的是维护脚本，不是 ShunCode 官方源码版本，也不会修改安装器；**不能保证下一次升级永远不丢失改动**。升级后先检查，不要直接把旧 JS 文件覆盖到新版安装目录。

2026-09-17 的现场检查中，这两个文件都已具备原生 image 内容块，无需再次修改。该现场安装的完整文件、用户图片、浏览器数据、凭据与原始诊断日志不进入本次发布包。

## Windows 操作步骤

准备 Python 3.10+；实际应用/恢复还需要 `node` 命令可用。下载本 Release 的扩展 ZIP（包含维护脚本）或 Source code ZIP 并解压，或 `git clone` 后更新到最新 tag。在 PowerShell / CMD 中进入仓库根目录。

### 1. 找到当前安装的扩展目录

目标是含 `runtime` 与 `dist` 的 **ShunCode 内置扩展目录**，不是 DeepSeekPP 的浏览器扩展目录。例如：

```text
D:\shuncode\ShunCode\resources\app\extensions\shuncode
```

下面每条命令的 `--dir` 都要换成你的实际路径。也可设置 `SHUNCODE_EXTENSION_DIR`。脚本不会遍历整块硬盘猜安装位置。

### 2. 默认只读检查

```powershell
python tools/shuncode-read-image-patch.py --dir "D:\shuncode\ShunCode\resources\app\extensions\shuncode" --check
```

- `ALREADY`，退出码 **0**：两个已识别的 `read_image` 成功分支都返回 image 块；不改文件、不创建备份。继续第 4 步。
- `NEED`，退出码 **1**：识别到可补丁的已知旧分支；仍然未写文件。按第 3 步处理。
- `BLOCKED`，退出码 **2**：缺文件、重复/未知结构、哈希变化、权限或语法检查失败等。**停止，不要强行替换**；保留当前安装，提供产品版本、退出码和必要的脱敏错误信息，等待针对该版本更新维护脚本。

此检查判断“已知代码形状具备 image 块”，不等价于服务已重启、MCP 客户端已支持图片或 Web 已成功上传。

### 3. 仅 NEED 时恢复原生图像块

先保存工作，完全退出 ShunCode。用独立的 PowerShell/CMD 运行，不要在将被关闭的 ShunCode 内置终端操作。

```powershell
python tools/shuncode-read-image-patch.py --dir "D:\shuncode\ShunCode\resources\app\extensions\shuncode" --apply
```

脚本会：

1. 同时读取并预检两个文件，仅定位唯一 `READ_IMAGE_TOOL` 分支；不会因别的工具里有 `content.push({type:"image"...})` 就误报已修复。
2. 确认已知 success/metadata/content 锚点；未知结构拒绝写入。
3. 使用 Node 对两个候选结果作语法检查。
4. 将两份原文件和本地 `receipt.json` 备份到用户主目录下 `.deepseekpp-shuncode-backups/<时间-随机后缀>/`；可用 `--backup-dir` 指定**安装目录之外**的保存位置。
5. 写入前重核源哈希，逐文件临时写入并替换；普通写入异常时尝试恢复已替换文件。这不是跨文件断电原子事务，断电/磁盘故障仍可能需要人工恢复。

不要把备份文件夹或 receipt 提交到 GitHub：里面有完整安装文件与本机路径。脚本不关闭/启动程序，不改 ShunCode 设置，不改浏览器设置，也不代替安装器。

### 4. 重启、重连、重载两端

1. 重新启动 ShunCode，确认 MCP 服务/连接重新建立；若检查为 ALREADY 但产品刚覆盖安装，也应确保当前进程加载的是新磁盘文件。
2. 安装/更新 DeepSeekPP **Fix 3.3.10.35（1.14.0.40）**。浏览器 `edge://extensions` 或 `chrome://extensions` 打开开发者模式，加载 Release 的扩展 ZIP 解压后含 `manifest.json` 的目录。已有同目录安装可备份后更新该目录，再点“重新加载”；不要无故删除浏览器存储。
3. 关闭旧 DeepSeek 页面并新开 `https://chat.deepseek.com/`，确认已登录。旧页面可能仍运行旧 content script，单改磁盘文件不够。
4. 按 [中文使用指南](../USAGE-zh_CN.md) 配置 MCP；直接展示全部工具模式可保持工具暴露明确。Agent 运行时不要发“继续”打断它。

### 5. 用自己的非敏感小图验收

建议先用几十 KB 的 PNG/JPEG，放到当前允许访问的工作区，换一张不曾在文字中描述过的图，在新会话要求：

> 使用 read_image 读取工作区的 test-image.jpg。请根据实际图像描述主要内容和布局；若只得到文本或图片未上传，请明确说无法确认，不要猜测。

检查三件事：

- MCP 结果确有原生 image 块，而不是只有“读取成功”的文字。
- DeepSeekPP 的脱敏诊断 `dpp_read_image_diag_v7` 有 `capture → upload_start → upload_ok → request_refs → request_ack`，引用计数大于 0。不要粘贴完整浏览器存储或请求 headers；只摘取阶段、固定错误码、字节数/计数。
- 回答与图像的主要内容相符。若需要严格识图证明，应换未描述过的新图和新会话做盲测；已有会话背景可能影响回答。

只验证了原生 image 块、但没有 `upload_ok`，应排查浏览器后台上传/登录/PoW；`upload_ok` 但没有后续引用，应排查本轮生命周期和 completion 请求。原生检查 ALREADY 但 MCP 仍只有文本，应先检查进程是否重启、连接指向哪一实例及客户端是否保留 image 块，而不是继续叠加补丁。

## 回滚

仅当**同一安装版本、当前文件仍是本脚本写入的结果**时，保存工作并退出 ShunCode，然后执行：

```powershell
python tools/shuncode-read-image-patch.py --dir "D:\shuncode\ShunCode\resources\app\extensions\shuncode" --restore "C:\Users\你的用户名\.deepseekpp-shuncode-backups\时间-随机后缀\receipt.json"
```

恢复会验证 receipt 的安装位置、两个当前结果哈希及两份备份哈希。若已经覆盖安装成另一版本，必须拒绝回滚，不能用旧文件覆盖新产品。恢复后重启程序。异常断电留下 `prepared/failed` receipt 时，不自动套用，先逐文件核对或重新安装官方产品。

## 测试与边界

- `python tools/shuncode-read-image-selftest.py` 仅使用临时模拟目录，不修改实际安装。覆盖默认只读、作用域误判、未知结构、两个文件预检、备份/幂等/恢复、产品升级后的拒绝回滚、写入中途失败恢复、CRLF/BOM、语法错误等。
- 此维护脚本只支持明确识别的代码形状；如果新产品改为另一种实现，可能正确地返回 BLOCKED，需要适配，不能宣称通用自动修复所有 ShunCode 版本。
- 旧文档中的“128KB 通道上限”不是当前已证明的通用上限。当前一次真实验收为 **130×160、3043 B JPEG**；没有新增的大图、所有格式或 API 后端验收。
- DeepSeekPP v7 当前实现有本地大小/格式限制；实际可用大小还受 MCP、浏览器、DeepSeek 上传接口和模型影响。本说明不承诺扩大任何服务限制。

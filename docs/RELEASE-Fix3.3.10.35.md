# Fix 3.3.10.35（扩展版本 1.14.0.40）

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

日期：2026-09-17。安装步骤、验证范围和维护边界如下；分发文件及校验值见 GitHub Release。

## 本次更新

- **恢复 Web Agent 自动读图完整链路**：捕获当前运行的 `read_image` image 块，执行真实后台图片上传，取得文件 ID，并仅附加到当前会话的后续 completion。不是把 base64 或“已读图”的文字当成模型已看图。
- **修复真实后台权限入口**：只在所需白名单中加入 `UPLOAD_DEEPSEEK_IMAGE`，保留原 listener、发送方校验、解码器、handler 与上传服务。受信主页面上传不再错误依赖侧栏聊天开关；侧栏原行为保持。
- **收紧上传上下文**：检查 DeepSeek 顶层 active document、documentId、当前标签页/会话；认证、PoW、上传前后重新核对适用上下文。payload 不能伪造内部可信分支。
- **本轮生命周期与诊断**：运行隔离、取消/失效处理、去重、下一次请求文件引用和确认、固定错误码与 `dpp_read_image_diag_v7` 分级诊断。诊断不记录图像、base64、完整路径、凭据或原始网络异常。
- **ShunCode 覆盖安装维护**：提供默认只读的双文件检查、已知结构限定补丁、安装目录外备份、源哈希复核、语法预检及受保护回滚。不会发布完整 ShunCode 安装程序，也不承诺覆盖安装永久保留修改。
- **发布工程**：.34 → v6 → v7 的纯函数、哈希锁定重建；manifest 和中英文扩展名称统一到 .35/1.14.0.40；保留 55 个已有行为套件，仅调整版本门禁。新增可独立运行的读图、真实后台边界及维护工具测试。

## 已核实的现场结果

在本次正式版本号更新前，已经部署的 v7 **两个运行时代码文件**完成一次真实测试：

| 项目 | 结果 |
|---|---|
| 图片 | JPEG，130×160，3043 B |
| MCP 原生通道 | 独立 `read_image` 调用返回 image/jpeg 内容块 |
| 浏览器链路 | `run_ready → capture(1) → upload_start(3043 B) → upload_ok → request_refs(1) → request_ack(1)` |
| 任务 | 正常 complete，2 steps / 3 tool executions |
| 视觉核对 | 回答与缩略图主要构图大体相符 |

这不是严格盲测：已有图片和会话背景可能影响回答，缩略图也不支持所有精细颜色/细节判断。不把模型一句“通过”当成唯一证据；此次结论限定为该小 JPEG 的原生内容块、上传/引用/响应链路恢复。没有新增真实大图、所有格式或 API 后端验收。

**发布包的 content/background 与上述实测的 v7 文件逐字节相同**；正式版本只额外更新版本 metadata。

## 安装和覆盖安装后的恢复

- 浏览器扩展下载本 Release 的 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.35.zip`，解压并加载含 `manifest.json` 的目录。已有安装先备份；更新后点扩展“重新加载”，关闭旧 DeepSeek 页面并新开已登录页面。
- **ShunCode 覆盖安装后先 check，只有 NEED 才 apply**；不要把旧完整 runtime 文件覆盖进新产品。
- 具体 Windows 命令、退出码、退出/重启程序、备份与回滚：[ShunCode 维护指南](ShunCode-read_image-图像通道-改造与维护.md)。
- 常规 MCP 配置与操作：[中文使用指南](../USAGE-zh_CN.md)。

## 边界与安全说明

- 检查标签页 URL/会话不等于完整证明同 URL 下没有发生 document 替换；不作绝对同-document 撤销保证。
- 上传期间离开会话会拒绝返回/使用文件 ID，但不能撤销已经到达远端的 HTTP 上传。测试请使用非敏感图片。
- 本地代码的格式/大小限制不等于端到端服务保证，认证 headers 的存在也不证明凭据有效。
- 原生维护的双文件更新可在普通 I/O 异常时尝试回退，不是跨文件断电原子事务；未知新版结构拒绝写入，等待人工适配。
- 无浏览器设置重置、侧栏设置更改、ShunCode 进程自动重启或其它项目数据库/服务修改。发布包不包含用户图片、浏览器存储、凭据、原始诊断日志或完整 ShunCode 安装文件。

## 运行时代码校验

| 文件 | SHA-256 |
|---|---|
| `content-scripts/content.js` | `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4` |
| `background.js` | `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc` |

Release 附 `SHA256SUMS.txt` 校验可下载 ZIP。manifest 的 `key` 是扩展公开标识公钥，沿用原版以保持扩展 ID，不是用户私钥。

## 开发者重建与离线验证

Python 3.10+、Node 20+。从 Git clone 的最新 .35 代码运行，先将公开 .34 tag 导出到单独目录：

```bash
git fetch --tags
mkdir ../baseline34
git archive v1.14.0-fix3.3.10.34 | tar -x -C ../baseline34
python tools/apply-fix331035.py ../baseline34 ../rebuilt35
python tools/validate-fix331035.py --root . --baseline ../baseline34 --output ../verification35
```

两个输出目录必须事先不存在；baseline 不能作为输出目录。重建器仅复制已提交 baseline inventory 列出的扩展运行时文件，验证每个源文件哈希及三个 helper 哈希；不会扫描、复制实际 ShunCode 安装或浏览器用户数据。旧 v4/v5/v6/v7 安装补丁 CLI 不适用于本正式版，也不是升级步骤。

行尾也纳入重建：公开 .34 Git archive 的两个 JS 源为 LF，历史 Windows 实测/补丁锁为 CRLF；构建器明确重建这两个源的 CRLF 表示，再执行原有纯函数变换。新 .35 对两个目标 JS、manifest、中英文 locale 和历史后台 fixture 使用专门的 `-text` Git 属性，避免提交/下载时归一化破坏已验证字节。其它运行时文件沿用 .34 公开 archive 的字节。首次准备中的严格哈希检查曾在复制到发布仓库前识别该行尾差异并停止，没有将不匹配的候选发布。

可单独运行：

```bash
node tools/dspp-readimage-v7-selftest.js content-scripts/content.js
node tools/dspp-readimage-v7-boundary-selftest.js .
python tools/shuncode-read-image-selftest.py
```

后台 suite 从实际候选 background 提取 listener/权限/解码/服务代码，只有浏览器/外部网络依赖被 mock。`tools/fixtures/readimage-v6-background.txt` 是公开 .34 扩展 background 的 Windows CRLF 冻结文本（与实测 v6 逐字节相同），用于真实旧入口失败复现与白名单增量断言；**不是 ShunCode 安装文件**。

## 验证记录

- v7 部署前已有：自动读图与实际 Jz 22/22、真实后台边界 16/16、已有扩展回归 55/55、阶段工程检查 38/38；正式双文件部署后再次执行 22/22 与 16/16 均通过。六个 v7 维护代码诊断为 0 error / 0 warning。
- 新原生维护脚本离线测试：22/22 通过（临时模拟目录）。
- 正式 .35 门禁：**20/20 工程检查、6/6 JS 语法检查、22/22 自动读图、16/16 实际后台边界、22/22 原生维护、55/55 原有套件全部通过**（64 个测试进程均 exit 0）。100 个运行时文件与独立重建结果逐字节相同；相对公开 .34 基线仅 5 个运行时文件改变，manifest 除版本字段外不变，旧测试仅调整版本门禁。脱敏机器可读报告见 [fix331035-validation.json](fix331035-validation.json)。
- 当前实际 ShunCode 的两个目标文件由新维护脚本只读检查均为 ALREADY，before/after 哈希相同，没有重打补丁或重启用户程序。

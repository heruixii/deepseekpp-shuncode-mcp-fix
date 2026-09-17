# DeepSeekPP read_image v6 上传失败：运行时消息权限边界

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 本轮浏览器验收失败（优先于下方此前待验状态）**：磁盘仍为.36/1.14.0.41，GitHub发布不变；本轮22步/30工具，3次取得图像字节后上传被 runtime_message_unauthorized 拒绝，refs=0，2,168字节也失败。其余直接读图含4次文件不存在、6次网络错误，并非全部success。当前MCP小图复核返回原生image块，不能归因于ShunCode始终剥离。具体后台拒绝子条件及浏览器驻留版本未取证；阻塞仍被记为complete待修。本次仅核查，未改运行代码或发布新版。 详见 docs/mcp-deepseekpp-visual-blocker-20260917.md。
> 部署状态（脚本维护）：v8/.36正式磁盘已更新为1.14.0.41；content e66f24d5…f1ec，policy c8e843c8…c8c6，background不变。浏览器重载/新模型验收待进行，分发回执见v8文档；2026-09-17。

> **2026-09-17 v8 当前接手入口**：Fix3.3.10.36 / 1.14.0.41 已部署本机磁盘，修复视觉主动工作流与长未注册工具块误完成；48视觉/22读图/16后台/22原生维护/55旧回归、14工程/6语法通过，正式文件复测48/22/16通过。浏览器尚需用户重载，新模型SVG端到端未验证；GitHub已正式发布 Latest v1.14.0-fix3.3.10.36，提交16a9219ff8dbd3601fedecfb459d1d5431e04248；三个远端附件下载SHA-256及API digest一致。黑曜石已将奇思妙想整理为dspp：4当前入口+21历史原稿+1历史索引，53处链接修复、131处校验，原始备份保留，未推送私人笔记库。详见 docs/mcp-deepseekpp-visual-workflow-v8.md。下方旧版状态按历史阅读。

## 2026-09-17 现场结论

**v6 浏览器实测失败，已定位一个确定性阻断点：内容脚本无权调用既有上传命令。**

不是根据 `upload_failed` 猜测 DeepSeek 文件服务器故障。当前 `background.js` 在上传处理器之前拒绝了该消息。此次只读日志/源码取证并更新文档，未修改运行代码、未重载浏览器、未执行真实图片上传。

### 最新日志

只读快照：`D:/tmp/readimage-v6-upload-20260917-105431/`。

- 页面 localStorage LevelDB：复制13个文件，宽容解析6161个键，仅读取 `chat.deepseek.com` 的 `dpp_read_image_diag_v6`。
- 扩展存储 LevelDB：复制7个文件，解析20个键；只导出诊断/trace 类选定键供同机分析。
- 活跃数据库未修改；快照是逐文件 best-effort 复制，并非数据库锁定的一致性快照。
- CDP 9222/9223 均不可达；没有浏览器实时 Network/Console 抓包证据。

| epoch 毫秒 | stage | 数据 |
|---:|---|---|
| 1789613471379 | run_ready | web=true |
| 1789613478124 | tool_failed_or_truncated | count=1；不能单凭此键分清前次工具失败还是截断 |
| 1789613482867 | request_refs | count=0, warnings=1 |
| 1789613507078 | capture | count=1, rejected=0 |
| 1789613507080 | upload_start | bytes=3043 |
| 1789613507082 | upload_failed | count=1 |
| 1789613512281 | request_refs | count=0, warnings=1 |

后一次读图已成功捕获1张3043 B图片，图片提取没有被格式检查拒绝；上传开始后2毫秒失败，下一轮没有图片引用。

## 真实源码复现

文件：`D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3/background.js`。

- 顶层监听器：`CN(message) → wN(sender) → EN(message, senderContext)`；通过后才 `MR → typed handler → service.uploadImage`。
- `wN` 将 DeepSeek 顶层内容脚本归类为 `surface:"deepseek_content"`。
- `EN` 只允许该 surface 使用 `xN` 集合中的命令。
- `xN` **不包含** `UPLOAD_DEEPSEEK_IMAGE`。
- 因此 `EN` 抛 `RuntimeBoundaryError`，`DN` 返回 `{ok:false,error:"runtime_message_unauthorized"}`，不会执行上传处理器。

抽取当前文件的真实 `xN/EN/DN/B` 到 Node VM，输入相同命令的离线结果：

```json
{
  "surface": "deepseek_content",
  "allowed": false,
  "boundary_response": {"ok": false, "error": "runtime_message_unauthorized"},
  "detail": "Runtime command UPLOAD_DEEPSEEK_IMAGE is not authorized for DeepSeek content.",
  "upload_handler_reached": false
}
```

对照 `surface:"extension_context"` 允许通过。这个对照是离线权限函数测试，不是冒充发送方或绕过权限的浏览器操作。

v6 把所有失败回调归并为 `upload_failed`，没有保留该错误分类；因此**现场日志直接证明失败时序，真实代码复现证明当前命令必被边界阻断**，但不能声称日志本身记录了 `runtime_message_unauthorized`。

## 两项解释修正

1. `data_uri:"[image bytes omitted]"` 是 v6 的 `redact` 在回灌工具结果时替换二进制字段，不是证据表明 ShunCode 未返回字节。`capture count=1` 和 `upload_start bytes=3043` 反而说明扩展拿到了可提取的字节。
2. `upload_start` 在 content 中调用 `chrome.runtime.sendMessage` 之前记录，不等于 HTTP 上传请求已发出。此次阻断位于命令分发之前，不应先排查图片分辨率、DeepSeek 服务可用性或 PoW。

## 上一版验证缺口

v6 专项22/22和旧扩展55/55确实通过，但上传使用模拟的 `chrome.runtime.sendMessage`，没有把后台真实发送方权限门串进测试。这些结果只能证明所覆盖的状态/函数正确，不能证明完整浏览器链路可用。当前端到端状态从“未验收”更新为“已实测失败，待修复权限接线”。

## 下一步修复建议（尚未实施）

1. 需要改变此前保持不动的 `background.js`。只授权 `UPLOAD_DEEPSEEK_IMAGE` 这一条给已验证的 DeepSeek 顶层内容脚本；不跳过 `wN/EN`，不开放任意网页/iframe/其他扩展，不扩大全部命令权限。
2. 将上传命令接入浏览器当前 tab 再校验链（`RN/LN → aI/TN`），保留 runtime ID、origin、frame、active lifecycle、tab URL 检查，避免旧文档在导航后继续获准上传。
3. 保留图片 payload/大小/MIME 验证及现有鉴权、PoW；不要用伪造 sender 或替换全局权限判断来修复。
4. v6 错误报告增加固定枚举分类（例如 runtime_unauthorized、chat_disabled、auth_missing、upload_timeout、upload_failed），不记录原始错误正文、凭据、图片字节。
5. 新测试必须覆盖真实 sender/allowlist/typed decoder/上传服务接线；包括顶层允许、外域/子框架/错误扩展ID/非active文档拒绝、当前tab导航变化拒绝、原扩展页面保持可用。
6. 扩展两文件都需要 hash-lock/备份/回滚；维护工具也要更新，不能继续断言 background 永远等于旧哈希。
7. 权限门通过后仍可能暴露 `chat_enabled`、鉴权或 PoW 等下一层问题；这些目前未验证。最终仍以浏览器实际上传返回ID、completion携带同一ID、模型准确识图为验收。

## 变更记录

- 2026-09-17：根据用户报告读取新日志，确认3043 B图片捕获成功、2ms上传失败；源码离线复现内容脚本上传命令被运行时权限门拒绝；明确上一版测试覆盖缺口，同步更正当前验收状态。本次不修改扩展运行代码。

相关入口：`docs/mcp-deepseekpp-readimage-v6.md`、`docs/DeepSeekPP-read_image-自动读图-交接排查文档.md`、`docs/DeepSeekPP-Fix3-项目交接文档.md`。

### 2026-09-17T11:09:53+08:00 · read_image v7 apply

- content.js: 902208 B, SHA `76c02e472300316dd537af587dc3630d13a45ef3bde0b03aca189f7d640586d4`。
- background.js: 654147 B, SHA `4f89a4d8b8d92a0e8c8661fdc5fc3a1745f39e2de2fc3306e0b3d9e7c87e3abc`。
- 两文件备份为各自 `.v7_bak`（v6）；本操作含双文件语法校验和文档回执。
- 未修改侧栏开关、未重载浏览器、未进行真实图片上传；端到端验收仍待进行。


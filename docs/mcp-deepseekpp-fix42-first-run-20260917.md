# Fix 3.3.10.42 首次现场复盘（2026-09-17 21:59–22:04，loop `806d5ac7`，会话 `91f45bbd`）

- 取证：`D:/tmp/edsnap-331042-verify-2216`（扩展 LevelDB + `chat.deepseek.com` 页面 localStorage `dpp_read_image_diag_v7`）
- 结论：**.42 的目标（任务不再中断）达成；.42 的手段 A1（触发线）实际未生效、靠 B 兜底；模型"没看到图"是 `include_data_uri:false` + 扩展丢弃 `content[]` 图像块的组合，且模型的最终陈述与自己第 8 步的推理矛盾（它看到过一次 240px 参考图）。**

## 1. 任务本身：complete，17 步，0 次中断

| 指标 | .41（20:53–20:56） | .42（21:59–22:04） |
|---|---|---|
| loop 状态 | 3 × `unexecuted_work_limit_331036` | **complete**，`turn_decision=final` |
| 注入 ShunCode 工具 | 3–4 个、每轮漂移 | **6 个固定**：apply_patch, read_files, read_image, search_files, list_directory, run_command（`tool_execution_blocks.descriptorIds`；`web_response_diag.descriptorNames` 只保留前 12 条，勿据此判断） |
| 裸标签 / `unregistered_tool_tag_331033` | 4+4+4 | **0** |
| 产物 | 无 | `redraw_xDSdaD2nc2wDvwj.html`、`_shot_final.png` 落地 |

## 2. 但 A1 触发线没起作用（我的估算错误）

- 真实 ShunCode 15 工具的 `promptDescriptorCost` 合计 **49,240 B**（用 live `fix3-policy.js` 对真实 tools/list 重算），仍 > .42 的 48,000 → 服务器仍被自动降为 adaptive（`descriptorCount=18` = 9 本地 + 6 ShunCode + 3 capability，而非 24）。
- 错因：我在沙盒估算时用 96 B/工具的固定开销，policy 实际是 `gd=1024`，15 × 928 ≈ 13.9 KB 的差额被漏算。**.42 文档中"35,883 B"是错的，应为 49,240 B。**
- 之所以仍成功：.42 的 B（8 槽 / 24 KB + read_image floor）兜住了——6 个核心工具全程在表，run_command 与 read_image 同在。
- 修正方向：触发线 48,000 → **64,000**（.43），或用户在侧边栏显式选「直接」（.42 起被尊重，不会再被覆盖）。

## 3. "read_image 只返回元数据"的真实链路

`dpp_read_image_diag_v7` 时间线（页面 localStorage）：

| 时间 | 调用 | 结果 | v7 通道 |
|---|---|---|---|
| 21:59:50 | `read_image` 原图 webp（774 KB） | `network error`（ngrok/超时） | tool_failed |
| 21:59:58 | 同上 + `include_data_uri:false` | **`MCP response exceeded 128000 bytes`**（`content[]` 里仍带 image 块，base64 ≈ 1 MB） | tool_failed |
| 22:00:36 | `_ref_tiny.jpg` 240px + `include_data_uri:false` | ok，仅元数据 | **no_image_data** |
| 22:00:46 | `_ref_tiny.jpg` + `include_data_uri:true` | ok | **capture 1 → upload_ok 6699 B → request_refs 1 → request_ack** |
| 22:01:10 | `_ref_mid.jpg` 500px + `include_data_uri:false` | ok，仅元数据 | no_image_data |
| 22:03:34 | `_shot_final_small.jpg` 截图 + `include_data_uri:false` | ok，仅元数据 | no_image_data |

- 第 8 步模型 reasoning 原文："**Now I can see the reference image.** … 5 characters … Fate/Grand Order style … white coats with black bows, light blue background …" —— 22:00:46 那次**视觉通道端到端成功**（.35–.41 以来第二次现场确证，第一次 19:53）。
- 之后模型为规避 128 KB 上限改用 `include_data_uri:false`，此后每次都 no_image_data；最终答复"多次尝试、降采样到 240px 仍无图像数据"**与事实不符**：240px 那次 `include_data_uri:true` 是成功的，失败的是 `:false` 的几次。

### 为什么 `include_data_uri:false` 会丢图

ShunCode `read_image` 无论该参数如何都返回 `content:[{type:text},{type:image,data}]`；该参数只控制 `structuredContent.data_uri`。而扩展 `background.js` `Zo(e)`：**只要 `structuredContent` 存在就只取它、整段丢弃 `content[]`** → image 块从未到达 content.js 的 v7 `collect()`。所以：`include_data_uri:true` = 通道通；`:false` = 必然 no_image_data。这不是 ShunCode 的限制，是扩展结果归一化的取舍。

### 为什么原图直接读必失败

774 KB webp → base64 ≈ 1.03 MB > 服务器 `Max Result Bytes = 128000`。模型自己用 run_command 降采样是对的；240px/6.7 KB 与 500px/25 KB 都在限内。

## 4. 建议（.43 候选，未实施）

| 编号 | 改动 | 层 |
|---|---|---|
| A | 触发线 48,000 → 64,000 | fix3-policy.js（1 字面量） |
| B | `Zo()`：`structuredContent` 存在时，若 `content[]` 含 `type:image` 块，一并保留到 `output.content`（只加不减，非 image 块不变） | background.js |
| C | 视觉规则/重试文案：明确"`include_data_uri` 保持默认 true；原图 > ~90 KB 先降采样"；纠偏 `no_image_data` 时直接点名该参数 | content.js .36 文案 |
| D | `tool_failed_or_truncated` 时把 128 KB 上限写进给模型的 note，避免它误判为"工具不支持视觉" | content.js v7 note |

无需改代码的即时缓解：侧边栏 ShunCode → 暴露模式手选「直接」；`Max Result Bytes` 提到 1,500,000（仅影响 MCP 响应缓冲，v7 上传自身上限 8 MB）；提示词里写明"read_image 必须 include_data_uri:true，大图先降采样到 ≤600px"。

## 5. 诚实边界

- §2 的估算错误由我造成，.42 发布说明里的 35,883 B 数字不准确；已在交接文档 §7 记录。
- 本次是单任务单次；视觉端到端成功 2/2 次（19:53、22:00:46）均在 `include_data_uri` 为 true 时。

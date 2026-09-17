# DeepSeekPP（Web/Edge 扩展）图像通道 —— 改造调查与结论

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> 2026-09-17 调查。承接 `docs/ShunCode-read_image-图像通道-改造与维护.md`。
> 目标：让 `read_image` 读到的图像经 DeepSeekPP 通道真正进入模型视觉。
> **2026-09-17 修订：下文早期“当前通道=官方 API，因此不可行”的结论已被后续 Web 调用链核对推翻，不再作为当前根因。** 保留本文作历史调查；当前走 Web 文件上传与 `ref_file_ids`，v6 候选与验收边界见 `docs/mcp-deepseekpp-readimage-v6.md`。尚未证明端到端成功。

---

## 1. 运行版扩展定位（已确认）

| 项 | 值 |
|---|---|
| 宿主浏览器 | **Microsoft Edge**（非 Chrome/Quark） |
| 扩展 ID | `kdmpkkahkhdmdhfkdihkopikgcocbpbf` |
| 加载方式 | `location:4`（解压/开发者加载，非商店） |
| 扩展目录 | **`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`** |
| 版本 | `1.14.0.39` |

定位依据：`Edge/User Data/Default/Secure Preferences` 中该扩展
`location=4, path=D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3, from_webstore=false`。

---

## 2. 工具结果 → 模型 的实际数据流

```
模型(官方API) --toolCall--> 扩展执行工具 --> toolResult
   {role:"toolResult", toolCallId, toolName,
    content:[{type:"text", text: Xz(result)}]}
        ↓  $R() 构造请求体
   POST https://api.deepseek.com/chat/completions
   body: { model, messages:[{role, content}, ...], stream:true, thinking:{...} }
```

关键函数（均在 `content-scripts/content.js`）：

| 函数 | 位置(约) | 作用 |
|---|---|---|
| `Xz(e)` | `@578681` | 把 tool result 拍平成文本 |
| toolResult 构造 | `@575461` | `content:[{type:"text", text:Xz(e.result)}]` |
| `$R(e)` | `@513963` | 组装 API 请求体，`messages.map(e=>({role,content}))` 直接透传 |
| `qR()` | `@512501` | 声明模型能力：`input:["text"]` |

---

## 3. 根因（两处，缺一不可）

### 根因 A：图像块在 `Xz()` 被丢弃
```js
function Xz(e){
  let t = e?.content;
  return t ? t.filter(e => e.type === "text")   // ← 只保留 text
             .map(e => e.text).join("") : "";
}
```
即便 `read_image` 返回了 `{type:"image", data, mimeType}` 内容块，
这里也会**过滤掉**，只留下文本（含被截断的 base64 字面量）。

### 根因 B：模型端点声明只支持文本
```js
qR(){ return KR.map(e => ({
  id:e, name: e==="deepseek-chat" ? "DeepSeek Chat (Web)" : "DeepSeek Reasoner (Web)",
  api:WR, provider:GR, baseUrl:"", reasoning: e==="deepseek-reasoner",
  input: ["text"],          // ← 仅文本，不支持图像
  ...})) }
```
且实际请求打到 `https://api.deepseek.com/chat/completions`。
**该端点/该模型不接收图像输入。**

> 结论：**只改 `Xz()` 保留图像块是不够的** —— 下游模型端点根本不接受图像。

---

## 4. 可行改造方向（择一）

### 方案 1：接多模态端点（扩展已内置入口）
扩展设置里已有 **"Multimodal API"**（`multimodalApi` / `multimodalApiDescription`：
“Configure OpenAI image analysis, Gemini video analysis, and custom request URLs for
the built-in Multimodal MCP”）。
- 思路：让 `read_image` 的图走该多模态子通道分析，把**文字描述**作为 tool result 文本
  回灌主对话。这是**成本最低、且不依赖主端点支持视觉**的方案。
- 落点：Multimodal MCP 配置 + `Xz()` 之前的分流。

### 方案 2：主对话改用支持视觉的模型/端点
- 需 `qR()` 里 `input` 增加 `image`，`$R()` 允许 `content` 为数组
  `[{type:"text"},{type:"image_url",image_url:{url:"data:..."}}]`，
  并在 `Xz()`/toolResult 处保留 image 块。
- 前提：所选端点/模型真支持视觉（DeepSeek 官方 chat/completions 目前不支持）。

### 方案 3：维持现状 + 明确降级
- 在工具结果文本里保留“已读取图像（元数据）”，不声称模型能看图。

---

## 5. 改造落点清单（若走方案 1/2）

| 目标 | 文件 | 位置(约) | 动作 |
|---|---|---|---|
| 保留图像块 | content.js | `Xz()` @578681 | 不 filter 掉 `type:"image"`，或改走多模态分流 |
| toolResult 携带图像 | content.js | @575461 | content 数组含 image 块 |
| 请求体支持数组 content | content.js | `$R()` @513963 | 允许 `content` 为 parts 数组 |
| 模型能力声明 | content.js | `qR()` @512501 | `input` 增加 `image`（方案 2） |

⚠️ 该目录是 **Edge 解压加载的运行版扩展**；改动后需在 `edge://extensions` 重新加载。
升级/替换目录会覆盖，需重做。

---

## 6. 与 ShunCode 原生通道的对比

| 通道 | 图像能否进模型 | 原因 |
|---|---|---|
| ShunCode 原生 chat | ✅ | `agent-host.js` 有 image_url 注入，且其模型端点支持视觉 |
| **DeepSeekPP（Edge）** | ❌ | `Xz()` 丢弃图像 + 主端点 `input:["text"]` |

---

## 7. 方案 2 的前置条件与当前阻塞（2026-09-17 实测）

方案 2（让 `read_image` 的图经主对话进模型）需要**同时**满足，缺一不可：

1. **扩展侧代码**：`Xz()` 保留 image 块、toolResult content 数组化、`$R()` 允许数组 content、
   `qR()` 的 `input` 增加 `image`。
2. **模型/端点支持视觉**：主对话当前走 `https://api.deepseek.com/chat/completions`，
   声明 `input:["text"]` —— **不接收图像**。
3. **或改走扩展内置 Multimodal Vision MCP**（`analyze_images`，nativeHost
   `com.deepseek_pp.multimodal`）把图分析成文本回灌。

### 当前实测阻塞
| 检查 | 结果 |
|---|---|
| `com.deepseek_pp.multimodal` native host 是否注册 | ❌ 未注册（Edge `NativeMessagingHosts` 仅有 `com.quark.hostclient`） |
| 扩展目录是否自带 host 程序 | ❌ 未找到任何 `*host*`/`*multimodal*`/`*.exe` |
| Multimodal Vision server 默认状态 | ❌ `enabled:false`（需在 MCP 页手动开启并配 allowlist） |
| 主对话模型端点 | ❌ `input:["text"]`，`api.deepseek.com/chat/completions` 不支持图像 |

> **结论**：仅靠改扩展代码**不足以**让视觉生效。必须先补齐
> ①multimodal native host 程序并注册 ②在设置里配好多模态 API（OpenAI 图析 key / base URL）
> ③在 MCP 页启用 Multimodal Vision 与 `analyze_images`。这些是**运行环境依赖**，非纯代码改造。

### 现成可行的“使用视觉能力”路径
用户把图片**直接粘贴**进对话时，走 DeepSeek 页面原生多模态上传，**模型可直接看到**
（历史会话已实测）。这条路径无需任何扩展改造，是当前唯一确定可用的视觉入口；
`read_image` 工具读本地图的自动视觉则在上述前置条件满足前不可用。

#### 2026-09-17 复验（方案 A 确认可用）✅
用户在本会话直接粘贴 `xDSdaD2nc2wDvwj.webp`（动漫 date 服设定图），模型**成功看到**并准确描述：
- 5 个形象：金发短发红眼少女的 4 个视角（正面全身/背面全身/低头大蝴蝶结特写/半身特写）+ 左下角黄色小鸡；
- 服装细节：白色双排扣大衣式连衣裙、黑蝴蝶结、黑蕾丝裙边、黑色过膝袜 + 黑色高跟短靴；
- 文字：中间方框「デート服」、左下角圆圈⑨与手写日文。

→ **结论**：`用户粘贴图` 与 `read_image 工具读图` 是**两条不同通道**：
| 路径 | 图像进模型 | 说明 |
|---|---|---|
| 用户直接粘贴 | ✅ 可见 | DeepSeek 页面原生多模态上传，image block 保留 |
| `read_image` 工具 | ❌ 不可见 | `Xz()` 丢弃 image 块 + 主端点 `input:["text"]` |

因此“使用视觉能力”当前**唯一可靠方式 = 用户粘贴图**；工具自动读图需先补 §7 前置条件。

---

## 8. 变更记录
- 2026-09-17：定位运行版（Edge 解压加载）；查明双根因；给出三方案与落点清单。
- 2026-09-17：查明方案 2 的前置条件与阻塞（native host 未注册、端点不支持视觉）。

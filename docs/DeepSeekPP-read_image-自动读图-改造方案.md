# DeepSeekPP `read_image` 自动读图 —— 改造方案（复用原生上传通道）

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 维护修订**：本文件保留 v3/v4 方案演进，旧实施状态与“下一轮一定生效”等推断不再代表当前状态。当前实现/验收/回滚以 `docs/mcp-deepseekpp-readimage-v6.md` 为准：v6 候选覆盖首次结果与循环结果，await 上传、按运行隔离；尚未浏览器验收。`DPP_AGENT_SYNTHETIC_REF_FILES_337` 是已有修复中的空引用隔离变量，不能仅凭名称称为官方自动读图入口，本轮保持其为空。

> 2026-09-17。承接 `docs/DeepSeekPP-图像通道-改造调查.md`。
> 目标：让 `read_image` 工具读到的本地图，模型**自动可见**（无需用户手动粘贴）。
> 核心思路：**复用「用户贴图可见」的同一通道——DeepSeek 原生文件上传 + ref_file_ids。**

---

## 1. 可行性依据（决定性）

已实测：**用户直接粘贴图片，模型能看到**。底层机制（源码确认）：
1. 图片经 `/api/v0/file/upload_file` 上传；
2. 返回 **file id**；
3. 聊天请求体用 **`ref_file_ids`** 引用 → 模型原生多模态看到图。

证据（`content.js` completion body @284965）：
```js
body: JSON.stringify({
  chat_session_id, parent_message_id, model_type, prompt,
  ref_file_ids: e.refFileIds,        // ← 图像引用
  thinking_enabled, search_enabled, action:null, preempt:false
})
```
**既然该通道对"用户图"有效，对"工具读到的图"同样有效——只需让 read_image 的图也上传并加入 ref_file_ids。**

---

## 2. 现状：read_image 为何看不到

```
read_image(MCP) → {content:[{type:"text",...},{type:"image",data,mimeType}]}
   ↓  Xz(e) 只保留 type==="text"          ← 图像块在此丢弃
   ↓  toolResult.content=[{type:"text",text}]
   ↓  $R() → messages:[{role,content}]     ← 纯文本
   ↓  POST api.deepseek.com/chat/completions  ← 不走页面上传/ref_file_ids
```
两处偏差：①`Xz()` 丢弃图像；②read_image 的图未走页面上传，故无 `ref_file_ids`。

---

## 3. 改造方案 R：复用页面上传 + ref_file_ids

### 3.1 目标数据流
```
read_image 返回 image 块
  ↓ 检测 image(base64+mimeType)
POST /api/v0/file/upload_file → file_id
  ↓
file_id 记入当前请求 refFileIds
  ↓
completion 请求体 ref_file_ids:[file_id,...] → 模型原生看到图
```

### 3.2 落点（`content-scripts/content.js`）
| 步骤 | 位置(约) | 动作 |
|---|---|---|
| A 保留图像块 | `Xz()` @578681 | 不再只 filter text，单独取出 image 块 |
| B 上传图像 | 复用 `uploadFile` 封装 | base64→ 得 file_id |
| C 注入引用 | completion body @284965 | file_id 并入 `ref_file_ids` |
| D 传入请求 | `$R()` @513963 | 携带 refFileIds |

### 3.3 约束
- **大小**：上传上限 8MB；且 MCP 通道 base64 >~128KB 会被截断 → 先降采样（见 `docs/ShunCode-read_image-图像通道-改造与维护.md` §5.1）。
- **格式**：仅 image/*，PNG/JPEG 优先。
- **时序**：上传异步，须在构造 completion 请求前完成拿到 file_id。
- **回退**：上传失败退回纯文本，不阻断对话。

---

## 4. 方案对比

| 方案 | 机制 | 依赖 | 评价 |
|---|---|---|---|
| **R（本方案）** | 复用 upload_file + ref_file_ids | 无额外依赖，复用现成通道 | ✅ 推荐，与"用户贴图"同通道 |
| Multimodal MCP | native host 图析→文本 | 需装 com.deepseek_pp.multimodal host + OpenAI key | ❌ 依赖缺失 |
| 主端点直传 image_url | 改 qR()/$R() 数组 content | 需端点支持视觉 | ❌ 端点不收图 |

---

## 5. 实施前提与风险
1. 改的是 **Edge 解压加载运行版扩展**（`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`）→ 改后 `edge://extensions` 重载；更新会覆盖。
2. 上传请求格式**已查清**（见 §8）。
3. `Xz()` 改动须不破坏纯文本工具结果。
4. 上传引入额外网络请求，失败需安全回退。

---

## 6. 下一步
1. 在 `Xz()`/toolResult 处检测 image 块；
2. 调用 `gA()` 上传得 file_id；汇入 completion 的 `refFileIds`；
3. 用小 PNG 端到端验证模型能看到；
4. 成功后补降采样与失败回退。

---

## 7. 变更记录
- 2026-09-17：方案设计；确认真实可用通道=页面上传+ref_file_ids；反查 uploadFile 封装。
- 2026-09-17（重要修正）：**方案 A（仅改 `Xz()` 保留 image 块）单独无效**。见 §9。

---

## 9. ⚠️ 重要修正：为何"仅保留 image 块"无效

实施前核对消息流发现：

**当前 DeepSeekPP 走 Web 模式**，`Hc()`（content.js @284684）发 completion 时：
```js
body: JSON.stringify({
  chat_session_id, parent_message_id, model_type,
  prompt: e.prompt,              // ← 纯文本
  ref_file_ids: e.refFileIds,    // ← 图像只在这里引用
  thinking_enabled, search_enabled, action:null, preempt:false
})
```
**body 里没有 `messages`、没有图像数组。**

工具结果回灌模型的方式是：`continueWithToolResults` 把结果拼成
`[TOOL_RESULTS] {toolResults} [/TOOL_RESULTS]` **文本**，作为下一轮 `prompt` 发出。
→ 即使 `toolResult.content` 里保留了 `{type:"image"}` 块，最终仍只被**序列化成文本**，
  图像不会进模型。

**因此：**
- ❌ 仅改 `Xz()`/toolResult 保留 image 块 **无效**（`tools/dspp-readimage-autopatch.py`
  的 Anchor A 属此类，**不应单独应用**）。
- ✅ 唯一可行：**把 read_image 的图上传得 file_id → 注入下一轮 completion 的
  `ref_file_ids`**（来源 `turnDefaults.refFileIds` @505670）。

**该正确路径的代价：**
1. 跨 `background`（上传 `gA`）+ `content`（注入 refFileIds）两上下文；
2. 异步：须在构造下一轮 completion 前完成上传；
3. 跨轮：ref_file_ids 属"下一轮"请求；
4. **改后需 `edge://extensions` 重载才生效 → 会中断当前对话 → 无法在本会话内验证。**

→ 风险与复杂度显著高于原估。建议在**不依赖当前对话**的独立时段实施并离线验证。

---

## 10. 正确路径实施规格（v2，全部原语已现成）

### 10.1 已确认的现成原语
| 原语 | 位置 | 说明 |
|---|---|---|
| 上传 | `background.js` 消息 **`UPLOAD_DEEPSEEK_IMAGE`** | payload `{dataUrl,name,mimeType,sizeBytes}`；返回含 file id |
| 上传实现 | `gA()`（background.js @494996）| `POST /api/v0/file/upload_file`，multipart 字段 `file` |
| 引用线程 | `content.js` `refFileIds`（20 处）| 最终进入 `Hc()` 的 `ref_file_ids` |
| 注入点 | `turnDefaults:{modelType,refFileIds,thinkingEnabled,searchEnabled}` @565835 | 每轮 completion 的 ref_file_ids 来源 |
| 捕获点 | `content:[{type:`text`,text:Xz(e.result)}]` @575399 | 工具结果构造处（含 image 块） |

### 10.2 实施步骤（在 content.js，2 处）
**① 捕获并上传（tool_execution_end 附近）**
- 检测 `e.result?.content` 中的 `{type:"image",data,mimeType}`；
- 组装 `dataUrl = "data:"+mimeType+";base64,"+data`；
- `chrome.runtime.sendMessage({type:"UPLOAD_DEEPSEEK_IMAGE",payload:{dataUrl,name,mimeType}})`；
- 把返回的 file id 暂存模块级 `pendingRefFileIds`（Promise/数组）。

**② 注入下一轮（turnDefaults 构造处）**
- `refFileIds:[...l.refFileIds, ...已就绪的pendingRefFileIds]`；
- 注入后清空 `pendingRefFileIds`（仅用一次）。

### 10.3 必须处理的时序
- 上传是**异步**的；须保证在下一轮 completion 构造前 resolve。
- 稳妥做法：在 tool 结果 → 下一轮的间隙 await（或让 pending 以 Promise 形式在 turnDefaults 前 await）。
- 失败回退：上传失败则不加 ref_file_ids，退化为纯文本（不阻断对话）。

### 10.4 验证与回滚
- 改后：`edge://extensions` 重新加载扩展（**会终止当前对话**）；
- **另开会话**：`read_image` 读一张 ≤几百 KB 的 PNG，观察模型能否描述画面；
- 回滚：`_dspp_backup/content.js.bak` 覆盖回去即可。

> **结论**：因验证必须重载扩展、无法在当前会话内完成，本改动**应在独立时段**执行。
> `tools/dspp-readimage-autopatch.py` 已更新为 v2（默认 `--check`，需显式 `--apply` 才改）。

---

## 11. 实施结果（2026-09-17 已应用）

### 已执行
- 补丁 v3 已 **apply 到运行版** `content.js`；哈希 `6657748d…` → `f4090f28…`。
- **语法校验通过**：`node --check` = 0（脚本内置"apply 后自动校验、失败回滚"安全网）。
- 标记就位：`DPP_READIMAGE_AUTOVISION`×1、`UPLOAD_DEEPSEEK_IMAGE`×1、`DPP_RIF`×6。
- 备份：`content.js.dspp_bak`（=原始 6657748d…），可一键回滚。
- **当前对话仍由已加载的旧代码服务**（扩展未重载）→ 本会话不受影响。

### ⚠️ 遗留：异步时序风险（功能可能不完全生效）
实现为"上传完成回调 → push 到 `DPP_RIF` → 下一轮 turnDefaults 消费"。
但上传是**异步**的，而下一轮 completion 可能**紧随其后**发出：
- 若 file_id 未就绪 → 该轮 `ref_file_ids` 为空 → read_image 图**当轮进不去**；
- 因此**功能可能只在后续某轮才生效，或完全不生效**（取决于时序）。

**这是已知局限，需重载扩展 + 实测后迭代**（例如改为在 tool→turn 间隙显式 `await` 上传 Promise）。
回滚方法：`cp content.js.dspp_bak content.js` 后重载。

### 待用户操作
1. 到 `edge://extensions` **重新加载** DeepSeekPP；
2. **另开新会话**：`read_image` 读一张 ≤几百 KB 的 PNG；
3. 观察模型能否描述画面 → 反馈结果以决定是否需迭代时序逻辑。

### 附：更优注入点线索（供迭代参考）
扩展内**官方已预留**一个合成注入变量：
- `var DPP_AGENT_SYNTHETIC_REF_FILES_337 = []`（@803850）
- 在 agent 请求构造处被用作 `refFileIds: DPP_AGENT_SYNTHETIC_REF_FILES_337`（@806344）

该变量名即"合成的 ref files"，是**为 agent 注入文件引用的官方入口**。
若当前补丁（turnDefaults @565871）时序不理想，迭代方向为：
**上传得 file_id 后 push 进 `DPP_AGENT_SYNTHETIC_REF_FILES_337`**，而非自造 `globalThis.DPP_RIF`。
（注：其为模块作用域 `var`，注入代码须位于同一作用域内才可直接引用。）

---

## 8. `uploadFile` 完整封装（已反查，background.js @494996）
```js
async function gA(e, t){                 // e.file=File, e.filename, e.clientHeaders, e.powHeaders, e.modelType
  if(!e.file.type.startsWith("image/")) throw ...;   // 仅图片
  if(e.file.size > 8388608) throw ...;               // ≤ 8MB
  let n = new FormData;
  n.append("file", e.file, e.filename);              // multipart 字段名 = "file"
  let r = await HA(LO("uploadFile", {
    credentials: "include",
    headers: { [iA]:"1", ...e.clientHeaders, ...e.powHeaders,
      "x-thinking-enabled":"0", "x-model-type":HO(e.modelType),
      "x-file-size":String(e.file.size) },
    body: n
  }), "DeepSeek file upload", "upload", {signal:t});
  i = await VA(r, ...); a = i?.data;
  o = MA(a?.biz_data ?? a?.bizData ?? i?.biz_data ?? i?.bizData);   // file 对象
  if(zA(a,i)) throw new VT("auth token rejected ...");
  if(!r.ok || a?.biz_code !== 0 || !o) throw ...;
  return vA(o, e.clientHeaders, t);                  // 返回含 id 的 file 对象
}
```
- **端点**：`/api/v0/file/upload_file`（POST multipart）
- **字段名**：`file`
- **鉴权**：`credentials:"include"` + `X-DPP-Bypass-Hook:1` + pow/client headers（会话 cookie）
- **限制**：仅 image、≤ 8MB
- **返回**：`biz_data`（经 `MA()` 规整），含 file id → 供 `ref_file_ids`
- 另有 `_A(fileIds)`：`GET fetchFiles?file_ids=...` 取元数据

> 方案 R 的两个原语（**上传**、**ref_file_ids 引用**）均已在扩展内现成可用；
> 改造只需把 image 块接到 `gA()` 上传，并把 file_id 汇入 completion 的 `refFileIds`。


---

## 10. v3 补丁实施记录与回滚（2026-09-17）

### 10.1 v3 做了什么（已应用过，后回滚）
在 `content.js` 的 `tool_execution_end` 处：
- 检测 tool result 里的 `{type:"image"}` 块；
- 经 `chrome.runtime.sendMessage({type:"UPLOAD_DEEPSEEK_IMAGE", payload:{dataUrl,name,mimeType}})` 上传；
- 把返回的 file id 推入 `globalThis.DPP_RIF`；
- 在 completion 请求体 `refFileIds` 处 `DPP_RIF.splice(0)` 并入下一轮。

### 10.2 缺陷（导致功能不生效）
`background.js` 的 `UPLOAD_DEEPSEEK_IMAGE` 处理器 `bP()` **强校验**：
```js
if(i<=0) throw Error(`${n} is empty.`);   // i = payload.sizeBytes
```
v3 的 payload **未带 `sizeBytes`** → 上传必抛错 → file id 永远拿不到 → 方案 R 不生效。

### 10.3 处置
- 运行版 `content.js` **已回滚为原始**（sha256 = `6657748d…`，890814 B，`node --check` OK，补丁标记全部归零）；
- v3 补丁版归档至 `_dspp_backup/content.js.v3_patched`（891570 B）供参考；
- 运行版目录现仅剩原始 `content.js` + `content.js.dspp_bak`。

### 10.4 v4 修正方向（待授权后再动手）
1. `UPLOAD_DEEPSEEK_IMAGE` payload **补 `sizeBytes`**（由 base64 长度推算：`Math.floor(dataUrl.length*3/4)` 或解码后字节数）；
2. 校验返回 id 的取值路径与 `bP()` 真实返回结构一致（需再确认 `uploadImage` 的返回字段名）；
3. 或改用扩展**官方已预留**的 `DPP_AGENT_SYNTHETIC_REF_FILES_337` 注入通道（@803850 定义，@806344 用于 refFileIds），风险更可控。

> 遗留时序风险：上传是异步，`sendMessage` 回调可能在 completion 请求发出**之后**才 push id → 需改为在构造 completion 前 `await` 上传完成（下一轮生效）。


---

## 11. v4 补丁已应用（2026-09-17）

### 11.1 相对 v3 的修正
| 项 | v3 | v4 |
|---|---|---|
| payload | 缺 `sizeBytes` → 被 `bP()` 拒绝 | **补 `sizeBytes`**（`Math.floor(b64.length*3/4)`，去 padding） |
| 取 file id | `r.fileId\|\|r.id\|\|r.file...`（猜测） | 按 `uploadImage` 返回 `{ok,file:{id,...}}` → **`r.file.id`** 优先 |
| 锚点 | 单点 | 双锚点：A=toolResult content，B=turnDefaults refFileIds |

### 11.2 已应用状态（本机运行版）
- 文件：`content-scripts/content.js`
- 新哈希：`e4269f28bb0b69a7021352b561b717306583fd2bd9ca66baccbf8a99e92c96e1`
- 备份：`content.js.v4_bak`（= 原始 `6657748d…`）
- 语法：`node --check` = **0（OK）**
- 标记：`DPP_READIMAGE_V4`/`DPP_RIF`/`sizeBytes` 合计 8 处

### 11.3 数据流（v4）
```
read_image toolResult {content:[text, image]}
  ↓ A 处：保留 image 块（不再只 Xz 文本）
  ↓ A 处：_dppUpload → chrome.runtime.sendMessage(UPLOAD_DEEPSEEK_IMAGE, payload{dataUrl,name,mimeType,sizeBytes})
  ↓ background bP() 校验通过 → uploadImage → {ok,file:{id}}
  ↓ 回调把 file.id push 入 globalThis.DPP_RIF
  ↓ B 处：下一轮 completion 的 refFileIds 并入 DPP_RIF（splice 清空）
  ↓ 模型经 DeepSeek 原生多模态"看到"图
```

### 11.4 遗留风险（诚实记录）
1. **时序**：上传异步，回调可能晚于本轮 completion；`DPP_RIF.splice(0)` 在下一轮才被取用，
   故**预期"读图当轮看不到、下一轮生效"**（非致命，但需知晓）。
2. **验证需重载**：改后须 `edge://extensions` 重载 → 中断当前对话 → **本会话无法验证**，
   需另开会话用 `read_image` 读小 PNG 端到端确认。
3. `sizeBytes` 为 base64 估算值（非解码精确值），仅用于通过 `>0 且 ≤8MB` 校验，足够。

### 11.5 回滚方法
```bash
cp "D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3/content-scripts/content.js.v4_bak" \
   "D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3/content-scripts/content.js"
# 再到 edge://extensions 重载
```
或运行 `python tools/dspp-readimage-v4-patch.py --check` 前先删标记（补丁脚本幂等，含标记即跳过）。

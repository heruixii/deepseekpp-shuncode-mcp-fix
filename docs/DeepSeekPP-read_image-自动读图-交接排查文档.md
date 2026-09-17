# DeepSeekPP `read_image` 自动读图 —— 交接排查文档

> **2026-09-17 目录分离**：本文件及全部 DSPP 文档/脚本/私有取证已从 `D:/learn/Athena计划` 迁出，独立于 Athena 计划维护；当前真源为公开仓库工作树 `D:/tmp/gh-deepseekpp`（docs/、tools/），私有取证在其 `local/`（已 gitignore，不上传）。

> **2026-09-17 本轮浏览器验收失败（优先于下方此前待验状态）**：磁盘仍为.36/1.14.0.41，GitHub发布不变；本轮22步/30工具，3次取得图像字节后上传被 runtime_message_unauthorized 拒绝，refs=0，2,168字节也失败。其余直接读图含4次文件不存在、6次网络错误，并非全部success。当前MCP小图复核返回原生image块，不能归因于ShunCode始终剥离。具体后台拒绝子条件及浏览器驻留版本未取证；阻塞仍被记为complete待修。本次仅核查，未改运行代码或发布新版。 详见 docs/mcp-deepseekpp-visual-blocker-20260917.md。
> 部署状态（脚本维护）：v8/.36正式磁盘已更新为1.14.0.41；content e66f24d5…f1ec，policy c8e843c8…c8c6，background不变。浏览器重载/新模型验收待进行，分发回执见v8文档；2026-09-17。

> **2026-09-17 v8 当前接手入口**：Fix3.3.10.36 / 1.14.0.41 已部署本机磁盘，修复视觉主动工作流与长未注册工具块误完成；48视觉/22读图/16后台/22原生维护/55旧回归、14工程/6语法通过，正式文件复测48/22/16通过。浏览器尚需用户重载，新模型SVG端到端未验证；GitHub已正式发布 Latest v1.14.0-fix3.3.10.36，提交16a9219ff8dbd3601fedecfb459d1d5431e04248；三个远端附件下载SHA-256及API digest一致。黑曜石已将奇思妙想整理为dspp：4当前入口+21历史原稿+1历史索引，53处链接修复、131处校验，原始备份保留，未推送私人笔记库。详见 docs/mcp-deepseekpp-visual-workflow-v8.md。下方旧版状态按历史阅读。

> 目的：向其他智能体完整交接本次改造的全部工程、改动、证据与未解问题。
> 目标功能：让 DeepSeekPP 扩展下调用 `read_image` 工具读到的本地图，模型能自动"看到"（无需用户手动粘贴）。
> 历史（v7修复前）：当前状态：**v6 浏览器实测上传失败**，已定位命令权限边界阻断。2026-09-17 最新实测：3043 B图片已捕获；upload_start→upload_failed仅2ms，下一轮ref count=0。抽取真实background权限门复跑，DeepSeek内容脚本调用UPLOAD_DEEPSEEK_IMAGE必被runtime_message_unauthorized拒绝，上传处理器未进入。上一版22/22模拟上传测试漏掉真实sender权限边界；离线通过不等于链路可用。本次仅取证/更新文档，未改运行代码。详见 `docs/mcp-deepseekpp-readimage-upload-boundary.md`。

---

## 0. 环境与关键路径

| 项 | 值 |
|---|---|
| 宿主浏览器 | **Microsoft Edge** |
| 扩展 ID | `kdmpkkahkhdmdhfkdihkopikgcocbpbf` |
| 加载方式 | `location:4`（解压加载，非商店） |
| 扩展目录 | `D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3` |
| 版本 | `1.14.0.39` |
| 被改文件 | `content-scripts/content.js`（minified，~890KB→892KB） |
| **未改**文件 | `background.js`（sha256 `ed5751c7…`） |
| 重载方式 | `edge://extensions` 重载（会中断当前对话） |

---

## 1. 底层机制（为什么要这么改）

### 1.1 DeepSeekPP 的两种模型通道
- **Web 模式（当前在用）**：`Hc()`（content.js @284684）发 `POST /api/v0/chat/completion`，
  body 仅 `{chat_session_id, parent_message_id, model_type, prompt, ref_file_ids, thinking_enabled, search_enabled, action, preempt}`。
  **没有 `messages`、没有图像数组**；工具结果被拼成 `[TOOL_RESULTS] {..} [/TOOL_RESULTS]` **文本**回灌。
- **API 模式**：`$R()`（content.js @513963）发 `api.deepseek.com/chat/completions`，有 `messages`。当前非此模式。

### 1.2 图像如何进模型（用户贴图能看到的原理）
1. 图片经 `POST /api/v0/file/upload_file` 上传 → 返回 **file id**；
2. 聊天请求体用 **`ref_file_ids`** 引用该 file id → 模型原生多模态"看到"图。

**结论**：要让 `read_image` 的图进模型，必须把图上传得 file_id，并注入下一轮 completion 的 `ref_file_ids`。

### 1.3 上传接口实现（background.js，未改）
```js
// background.js @494996 附近
async function gA(e,t){                       // e.file=File, e.filename, e.clientHeaders, e.powHeaders, e.modelType
  if(!e.file.type.startsWith("image/")) throw ...;
  if(e.file.size > 8388608) throw ...;        // ≤8MB
  let n=new FormData; n.append("file", e.file, e.filename);   // multipart 字段名 = "file"
  let r=await HA(LO("uploadFile",{credentials:"include",
    headers:{[iA]:"1", ...e.clientHeaders, ...e.powHeaders,
             "x-thinking-enabled":"0","x-model-type":HO(e.modelType),"x-file-size":String(e.file.size)},
    body:n}), ...);
  // 解析 biz_data → 规整为 {id,fileName,fileSize,mimeType}
  return vA(o, e.clientHeaders, t);
}
```
- 端点：`/api/v0/file/upload_file`（POST multipart），字段名 `file`
- background 暴露的 API（@628845）：`uploadFile:gA`、`createUploadPowHeaders`、`continueWithToolResults` 等
- **background 的消息处理器 `bP()`（@557952）强校验**：`dataUrl` 必须 `data:image/...`、`sizeBytes` 必须 `>0 且 ≤8MB`，否则抛错。
  → 这正是 v3 失败的原因（v3 未带 `sizeBytes`）。

### 1.4 工具结果的真实结构（决定从哪取图）
DeepSeekPP 工具结果对象为：
```js
{ok:true, name, callId, descriptorId, provider, summary, detail, output, ...}   // 见 background.js @105509
```
**图像数据在 `output` / `structuredContent.data_uri`，不在 `e.result.content`。**
（read_image 经 ShunCode Bridge 返回：`{path,status,format,mime_type,width,height,...,data_uri}`）

---

## 2. 本次所有改动清单

### 2.1 运行版扩展（`D:\learn\DeepSeekPP-1.14.0-ShunCode-MCP-Fix3\content-scripts\content.js`）
当前 **v5** 已应用：sha256 = `6ba876bd3b2cfa3f6328c328621d43d259a83f5298bb3f68d50ea21f9fe5c54b`

**锚点 A —— 工具结果上传（tool_execution_end 处）**：
原始：`content:[{type:`text`,text:Xz(e.result)}]`
改为：`/*DPP_READIMAGE_V5*/content:[{type:`text`,text:Xz(e.result)}],_dppUp:(function(){...})()`
其中 `_dppUp` 的完整逻辑：
```js
(function(){
  try{
    var _u=[];
    function _ad(d){ if(typeof d!=='string')return;
      var m=d.match(/^data:(image\/[a-z0-9.+-]+);base64,([\s\S]*)$/i);
      if(m)_u.push({mime:m[1],data:m[2].replace(/\s/g,'')}); }
    function _walk(o,dep){
      if(!o||dep>3)return;
      if(Array.isArray(o)){o.forEach(function(x){_walk(x,dep+1)});return;}
      if(typeof o!=='object')return;
      if(o.type==='image'&&o.data)_u.push({mime:o.mimeType||'image/png',data:o.data});
      _ad(o.data_uri);_ad(o.dataUri);_ad(o.dataURL);
      for(var k in o){try{_walk(o[k],dep+1)}catch(_e){}}   // ← 注意：此处遍历所有键
    }
    var R=e.result||{}; _walk(R,0);
    if(!_u.length)return 0;
    var _seen={}; _u=_u.filter(function(x){if(_seen[x.data])return false;_seen[x.data]=1;return true;});
    globalThis.DPP_RIF=globalThis.DPP_RIF||[];
    _u.forEach(function(x){
      var _s=String(x.data||'').replace(/=+$/,'');
      var _z=Math.max(1,Math.floor(_s.length*3/4));
      chrome.runtime.sendMessage({type:'UPLOAD_DEEPSEEK_IMAGE',
        payload:{dataUrl:'data:'+x.mime+';base64,'+x.data,name:'read_image',mimeType:x.mime,sizeBytes:_z}},
        function(r){
          try{ var id=r&&(r.file&&r.file.id||r.fileId||r.id||
                 (r.result&&(r.result.file&&r.result.file.id||r.result.id)));
               if(id)globalThis.DPP_RIF.push(id); }catch(_e){}
        });
    });
  }catch(_e){} return 0;
})()
```

**锚点 B —— 下一轮注入 refFileIds（turnDefaults 组装处）**：
原始：`refFileIds:o.refFileIds,thinkingEnabled:o.thinkingEnabled`
改为：
```js
refFileIds:(function(){var _f=(o.refFileIds||[]).slice();
  try{if(globalThis.DPP_RIF&&globalThis.DPP_RIF.length)_f=_f.concat(globalThis.DPP_RIF.splice(0));}
  catch(_e){}return _f;})(),thinkingEnabled:o.thinkingEnabled
```

### 2.2 工作区交付物
| 文件 | 说明 |
|---|---|
| `tools/dspp-readimage-v5-patch.py` | v5 幂等补丁脚本（--check/自动备份/自动从 v4_bak 恢复） |
| `tools/dspp-readimage-v4-patch.py` | v4 补丁脚本（已废弃） |
| `tools/dspp-readimage-autopatch.py` | 更早的 Anchor A 版（无效，仅 Anchor A） |
| `docs/DeepSeekPP-图像通道-改造调查.md` | 早期调查（含 §7 阻塞、§10 v3 回滚、§11 v4） |
| `docs/DeepSeekPP-read_image-自动读图-改造方案.md` | 方案文档（§1-§11） |
| `docs/DeepSeekPP-read_image-自动读图-交接排查文档.md` | 本文档 |

### 2.3 备份（回滚用）
| 文件 | sha256 前缀 | 内容 |
|---|---|---|
| `content.js.dspp_bak` | `6657748d…` | 原始 |
| `content.js.v4_bak` | `6657748d…` | 原始（v4 前） |
| `content.js.v5_bak` | `6657748d…` | 原始（v5 前） |
| `background.js` | `ed5751c7…` | 原始（**未改**） |

回滚：`cp content.js.v5_bak content.js` + `edge://extensions` 重载。

---

## 3. 版本演进与失败原因

| 版本 | 改动 | 结果 |
|---|---|---|
| v3 | toolResult 保留 image 块 + 上传（**未带 sizeBytes**） | ❌ 上传被 `bP()` 拒绝（`is empty`） |
| v4 | 修 sizeBytes；但只在 `e.result.content` 找 `{type:'image'}` 块 | ❌ **命空**：真实结构是 `{ok,..,output}`，图像在 `output/structuredContent.data_uri` |
| **v5** | 递归多来源提取 data URL（含 `data_uri`/`structuredContent`/`output`）+ sizeBytes | ❌ **仍失败**（下一轮模型仍看不到图） |

---

## 4. 未解问题（请排查）

**现象**：v5 应用 + 重载后，Agent 调用 `read_image` 读 `_readimg_clean.jpg`（208×256，6861B，返回 success+data_uri），
**下一轮** Agent 仍未收到任何图像块（只看到纯文本）。

**待排查的疑点（按概率）**：
1. **`tool_execution_end` 是否真的在 `mcp_invoke` 路径触发？** Agent 的 MCP 调用（`mcp_invoke`）可能不走此事件，导致 `_dppUp` 从未执行。→ 建议在 `_dppUp` 内加 `console.log('[DPP] _dppUp called')` 并在 F12 Console 观察。
2. **`e.result` 是否含 `data_uri`？** read_image 经 ShunCode Bridge 返回的可能是 `structuredContent.data_uri`，但 DeepSeekPP 侧 `tool_execution_end` 收到的 `e.result` 结构未知。→ 建议 dump `JSON.stringify(e.result).slice(0,500)`。
3. **`UPLOAD_DEEPSEEK_IMAGE` 上传是否成功？** 回调 `r.file.id` 是否拿到。→ Console 看是否有报错，Network 看 `upload_file` 请求。
4. **`DPP_RIF` 与 `refFileIds` 的时序**：`_dppUp` 是否在**同轮** completion 之后才 push？若 push 发生在 request 之后，则要再等一轮。→ 可临时把"下一轮"延长为"下下轮"再观察。
5. **`refFileIds` 注入点是否被用到**：锚点 B 改的是 `turnDefaults` 组装（@505670），但实际请求可能走 `Hc()` 的另一个调用点（@505315 / @505957）。→ 确认哪个 call site 真正发请求。

**关键排错手段**：
- F12 → Console：搜索 `[DeepSeek++]`、`_dppUp`、`UPLOAD_DEEPSEEK_IMAGE`、`is empty`、`not an image`；
- F12 → Network：过滤 `upload_file`，看是否发出、`biz_code` 是否为 0、是否返回含 `id`；
- 下一轮 completion 的 request payload：看 `ref_file_ids` 是否非空。

---

## 5. 复现与验证步骤
1. `edge://extensions` 重载 DeepSeek++；
2. 在 chat.deepseek.com 让 Agent 调 `read_image` 读一张 workspace 内小 PNG/JPEG（<128KB）；
3. **再发一条消息**（触发下一轮）；观察模型能否描述该图；
4. 全程开 F12 Console/Network 采集证据。

---

## 6. 变更记录
- 2026-09-17 收口：正式 content.js 已应用 v6，**901444 B**，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`；background 未改。最终隔离报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation-final/report.json`：专项22/22组、旧回归55/55套件、工程检查30/30；应用后实际目标专项再次22/22。5个维护代码文件诊断返回0 error/0 warning，3个Python文件语法通过。原始 .34 `.v5_bak` 与修改前 v5 `.v6_bak` 均已核验。未重载浏览器、未实际上传图片、未发布GitHub/ZIP；端到端识图仍待用户验收。
- 2026-09-17 批次三：隔离验证已通过：实际 helper/Jz **22/22 组**、扩展既有 **55/55 套件**，独立重建一致且树差异仅 content.js；默认只读、重复应用无写入、精确备份/回滚、输入/运行源篡改拒绝、坏语法拒绝、STALE_FILE 与模拟 I/O 失败回滚均通过。报告 `D:/tmp/DeepSeekPP-readimage-v6-20260917/validation/report.json`。追加部署状态自动维护行及其 apply/rollback 断言，避免未来回滚后页首仍称 v6 已部署；正式应用前再验证此维护逻辑。
- 2026-09-17 批次二：首个候选实际 helper + Jz 专项 **22/22 组通过**，Node 语法通过；候选 901444 B，SHA `251db07b3d1fc1aad31c492594b74bb11adac9143bde8032f120ce34d87d14d9`。增加 runtime/output 哈希锁、文档读取版本快照保护和独立离线验证器（55 个扩展旧套件 + patcher 篡改/回滚/事务故障测试）；接下来执行这些门。正式 content.js 仍为 v5；未重载/上传。
- 2026-09-17 批次一：确认首次 `toolExecutions` 未经过 v5 捕获事件；增加 v6 候选、运行隔离/await 上传/请求确认消费与离线测试。v5 实际字节锚点 B=506409、A=576270（旧偏移作废）；旧 v5 patcher 的写入入口已禁用。正式扩展尚未应用 v6；详见 `docs/mcp-deepseekpp-readimage-v6.md`。
- 2026-09-17：编写交接排查文档；汇总 v3/v4/v5 全部改动、机制、失败原因与待排查点。

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


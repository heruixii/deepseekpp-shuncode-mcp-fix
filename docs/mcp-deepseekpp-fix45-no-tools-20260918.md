# Fix 3.3.10.45 新日志诊断：网页端无 MCP 调用

日期：2026-09-18。范围：读取最新本机日志、核对 live、离线复现；未修改运行时代码、设置，未重载浏览器、部署或发布。

## 结论

最新故障不是旧版的 descriptorCount=9，也不是 ShunCode 断连。10:22–10:27 的三个网页请求在首次 CREATE_TOOL_AUTHORIZATION 阶段失败，工具增强未完成，原始正文照常发送；响应记录均 descriptorCount=0。已从 live 抽取 Nu() 并结合快照状态复现 .45 新增刷新分支的 JavaScript 暂时性死区（TDZ）错误。这是与现场阶段及缓存条件一致的确定性代码缺陷；浏览器持久化日志只记录 errorName=Error，没有保存具体异常消息，因此未声称取得浏览器现场堆栈。

## 版本与证据

- 仓库：D:/tmp/gh-deepseekpp。
- live：D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3，manifest 1.14.0.50 / Fix 3.3.10.45。
- background.js SHA-256：58a7affa5f8b492552ae2a35b58d028c6b41863c58a768a1d9d494b78bbd8aff。
- content-scripts/content.js SHA-256：a9b317dbf6d6ddaa7b0383906a803187ad579d102242d5606bc02a38a4afede5。
- 私有快照：D:/tmp/edsnap-mcp-check-20260918-103037。复制 Edge Default 的扩展 LevelDB 和 Local Storage/leveldb，跳过 LOCK；使用既有 ldb_extract.py 解析。浏览器保持运行，属于非原子热快照，不等于完整一致性数据库备份。
- 原始日志、离线脚本均留在上述私有快照目录，不进入公开仓库。

## 新日志时间线（本机时间）

会话 18b063d8-c06e-475e-8149-05b545fc86a0：

| 请求前缀 | 首次授权前 | content_augment_error | 响应时间 | 工具数 | 原文/增强后字符 |
|---|---|---|---|---|---|
| b86e2b17 | 10:22:11.202 | 10:22:11.226 | 10:22:38.934 | 0 | 881 / 881 |
| e5412b2f | 10:23:09.024 | 10:23:09.050 | 10:23:29.150 | 0 | 879 / 879 |
| e522a4a5 | 10:27:34.857 | 10:27:36.921 | 10:27:56.028 | 0 | 873 / 873 |

三个请求均有 content_after_multimodal，随后 content_augment_error（Error），未见 content_auth1_done；mw_augment_result 为 augmented=false。HTTP 200、streamFinished=true，不能据此判定工具链健康。

MAIN-world 日志：10:22 新页面 boot、bridge_open 均在；sync_state 与三次 send_hook 的 tools 均为 0，augment 的 active/bridge 均 true。不是单纯未加载扩展。

09:59 是另一个阶段：会话 b60bfa0b 首请求 descriptorCount=24，trace initialExecutions 中 find_files ok=true，之后 Agent 出现 generation_err 和工具意图纠偏，09:59:33 以零后续执行的错误停止。不要把它与 10:22 新会话未注入任何工具混为一谈。

## 服务器快照

- shuncode：enabled=true、execution.enabled=true、status=ready、lastError=null，工具缓存 health.toolCount=15；maxResultBytes=7000000，maxToolCount=32；暴露模式 direct 已落盘。
- Shell Local：enabled=true，但 execution.enabled=false；native host 未安装（Specified native messaging host not found.），缓存已过期。
- Multimodal Vision：enabled=false。

本次诊断连接的 MCP 列出 17 个工具，但扩展自身缓存为 15；只采用扩展现场清单解释 24=9+15，不把诊断客户端工具数直接套进浏览器。

## 根因代码与复现

Nu() 的刷新后合并逻辑：

```js
let [t, n] = await Promise.all([yc({includeSecrets: false}), Tc()]);
// ... 检查 enabled 服务器缓存是否缺失或过期，必要时 ju() ...
for (let t of c) {
  if (n.some(e => e.serverId === t.serverId)) continue;
  let n = i.get(t.serverId);
  // ...
}
```

内层 let n 的作用域覆盖整个 for 块；前面的 n.some 并不是访问外层缓存数组，而是在初始化之前访问内层变量，抛 ReferenceError。只要进入刷新分支且 Tc() 返回非空就会命中，即使 ju() 的失败已被 catch。当前 Shell Local 虽禁用执行，但仍 enabled=true，Nu() 的刷新筛选不排除它，因此其过期失败缓存足以触发全局目录失败。

调用链：content jZ → CREATE_TOOL_AUTHORIZATION → sz → oR / MCP provider → Nu；异常导致请求增强 catch。GET_TOOL_DESCRIPTORS 同样依赖该目录链，解释页面 tools=0。content 的 k$ 将运行时错误重新包装为 Error，且 preflight 仅保存 errorName，现场缺少具体消息。

离线实验从 live 原文抽取 Nu 和 Ho，使用快照服务器/描述符，mock yc/Tc/ju，不联网、不创建真实工具授权：

| 实验 | 结果 |
|---|---|
| 原函数 + 快照时刻 | ReferenceError: Cannot access 'n' before initialization；刷新对象为 Shell Local |
| 原函数 + 缓存均未过期的控制时刻 | 返回 15 个 MCP 描述符 |
| 仅测试副本将内层 n 改名 server + 快照时刻 | 返回 15 个 MCP 描述符 |

私有复现脚本：快照目录下 nu-live-repro.js、nu-rename-only-repro.js。第二个脚本只是诊断对照，不是已验收补丁。

## 为什么已有测试未发现

tools/dspp-mcp-cache-v45-selftest.js 对 Nu 只检查函数名、o=new Set、expiresAt<=r 等字符串存在，并未实际执行缓存刷新分支。语法检查也无法发现这一合法语法下的运行时 TDZ。因此 docs/RELEASE-Fix3.3.10.45.md 所记离线通过不能替代该行为回归。

## 建议修复与验收（未实施）

1. 消除 Nu 的变量遮蔽；补充缺失缓存、过期缓存、失败服务器与健康服务器并存的真实函数执行测试。
2. 同时检查刷新后合并逻辑：当前以旧 n 中存在 serverId 就跳过，可能导致 maxAgeMs 过滤掉的旧条目在刷新后仍不返回新描述符；不要只做变量改名就宣称自愈完整。
3. 补有边界、脱敏的授权失败诊断，避免只保留 Error；不得放松 sender、session 或工具授权检查。
4. 依据既有 builder/hash lock/validator 流程构建候选，先测试再部署。浏览器验收必须新页面新请求：content_auth1_done/增强完成，工具清单正确，且真实工具执行成功。
5. 禁用不使用的 Shell Local 可减少这一触发源，但其他缓存到期也能触发，不能作为完整修复；本轮未改设置。

参考：docs/RELEASE-Fix3.3.10.45.md、docs/RELEASE-Fix3.3.10.44.md、docs/mcp-deepseekpp-fix43-first-run-20260918.md。

## 后续实施回执

用户随后授权修复，已部署 Fix 3.3.10.46 / 1.14.0.51。Nu 刷新与合并、Sc 失效集合遮蔽已修复；新行为测试 18/18，validator 72 进程通过，live 62/62。浏览器验收仍待重载。完整变更与回退路径见 docs/RELEASE-Fix3.3.10.46.md；以上“未实施”描述保留为最初诊断时点记录。

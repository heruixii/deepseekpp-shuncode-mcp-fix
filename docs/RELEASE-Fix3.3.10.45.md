# Fix 3.3.10.45（扩展版本 1.14.0.50）

2026-09-18 · 修掉 .44 首次现场暴露的**“改 MaxResultBytes 后工具只剩 9 个”回归**，以及由此触发的**视觉前置空转**（`visual_preflight_331036 → reemit_tool_call ×3 → unexecuted_work_limit_331036`，零工具执行）。

## 版本

manifest `1.14.0.50` / `1.14.0 ShunCode MCP Fix 3.3.10.45`。相对 .44：`background.js` 4 处、`content.js` 4 处字面量 + `manifest.json` host_permissions 新增 ngrok；`fix3-policy.js` 与 `main-world.js` 与 .44 逐字节相同（`.43/.44` 同）。

| 文件 | SHA-256 |
|---|---|
| background.js | `58a7affa5f8b492552ae2a35b58d028c6b41863c58a768a1d9d494b78bbd8aff` |
| content-scripts/content.js | `a9b317dbf6d6ddaa7b0383906a803187ad579d102242d5606bc02a38a4afede5` |
| fix3-policy.js（= .44） | `39915841f22a165e1cc395e17d4fdff5651050c2d70c2e3bc6291ac3b26f38c5` |
| content-scripts/main-world.js（= .42/.43/.44） | `e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92` |

ZIP `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.45.zip` 13,984,236 B / 233 文件 / 162? 实际 233 文件（含 61 个 selftest），SHA-256 `b9e3e486815a23cd0c151b5a80cbcfaca948d4e37c2749592b3a44775aefda4b`。

## 根因（.44 首次现场，2026-09-18 08:42–08:53，快照 `edsnap-331044-verify-20260918-0941`）

详见 `docs/mcp-deepseekpp-fix43-first-run-20260918.md` 与本仓库 `tools/apply-fix331045.py` 顶部注释。

1. **配置变更触发工具缓存清空且无自愈。** `background.js Vc(e)` 把 `timeouts` 与 `limits` 也计入 `JSON.stringify`，用于判断服务器是否“发生实质变更”`Bc(n,o)`。用户在 ShunCode Bridge 页面把 `maxResultBytes` 从 128k 改为 7M（`updatedAt 08:43:13`）→ `Bc` 判 true → `Sc` 执行 `Ac(...toolCaches.filter(!i.has))` 清空该 server 的缓存，并把状态置为 `unknown/null/null`，**但没有调用 `ju(id)` 去重新发现**。`dpp_mw_bridge_diag_v10` 64 行显示 `tools:24` 健康直到 `08:42:54.952 sync_state tools:9`，之后一直 `tools:9` 到 `08:51:16 send_hook`。

2. **`Nu()` GET_TOOL_DESCRIPTORS 无自愈。** `Nu(e)` = `yc()` servers + `Tc()` toolCaches；缓存被清空后 `Nu` 直接返回 `[]`，`GET_TOOL_DESCRIPTORS` 只剩 9 个内置本地工具。`dpp_web_response_diag_331015` 2 行（08:50:26 req `a1f86ee8`、08:52:01 req `89ded92b`）均为 `descriptorCount 9`、`descriptorNames` 为 `memory_* / web_search / fetch / artifact_* / bundle_* / skill_* / memory_import_preview`，`httpOk true / streamFinished true`。`DPP_CORE_TOOL_FLOOR_331033` 1000 逻辑于是认为“已满足最低工具数”，不再触发补偿，但 `read_image` 缺失。

3. **视觉前置空转。** `content.js` `shouldStopAfterTurn` 中 `DPPVisualMissing331036 = !r && DPP_VISUAL_MISSING_331036(...)` 为 true 时，即使 `v` Map 里根本没有 `*_read_image`（tools:9），`getSteeringMessages` 仍会构造 `DPP_VISUAL_RETRY_331036`，其内部扫描 `v` 找 `*_read_image` → 空 → 裸 `read_image` nudge ×3，烧掉 `Ce.maxNudges=8 / DPP_TOOL_INTENT_NUDGE_MAX`，最后以 `unexecuted_work_limit_331036` 结束，零工具执行。`dpp_agent_turn_diag_331021` 11 行：`c70e6eb6` loopId，`visual_preflight_331036` → `reemit_tool_call` ×3 → `unexecuted_work_limit_331036`，`provider_terminal` 2 行 `bytes 122691 / 118972 / chunks 929 / nudge 2/3`。

## 修复

- **A1** `background.js Vc()`：`JSON.stringify` 只包含 `transport + headers + secrets`，不再包含 `timeouts / limits`。只有传输层/鉴权变更才应清缓存，`maxResultBytes` / `maxToolCount` / 超时属于执行期参数，不应触发失效。

- **A2** `background.js Sc()`：`_c.run` 事务内记录被清空的 `Set`，事务外对每个被清空且 `enabled` 的 id 调用 `ju(id).catch(()=>{})` 自动重发现。即使旧缓存已清，下一次 `Nu()` 也能拿到新缓存。

- **A3** `background.js Nu()`：自愈——遍历所有 `enabled` 服务器，若在 `toolCaches` 中无对应缓存、或 `maxAgeMs` 过期、或 `expiresAt <= now`，加入 `missing` Set；若 `missing` 非空，并行 `ju(id)`，再 `Tc()` 重取并把新增缓存的描述符合并进结果。`GET_TOOL_DESCRIPTORS` 在缓存丢失时不再静默返回 9。

- **A4** `background.js UPDATE_MCP_SERVER`：`Y('UPDATE_MCP_SERVER', async(n,r)=>{let i=await e.updateMcpServer(...); if(i){try{await e.refreshMcpServerDiscovery(n.id)}catch{}} return await t(r.tabId),i})`，任何配置更新后都尝试刷新发现，双保险。

- **B1** `content.js` 视觉守卫：`DPPVisualMissing331036` 增加 `&& !!DPP_VISUAL_TOOL_NAME_V41(v)`，只有当目录里真实存在 `*_read_image` 时才走 `visual_preflight` 纠偏；否则走新分支。

- **B2** `content.js` 缺失终局：新增 `DPPVisualToolAbsent331045 = !r && DPP_VISUAL_MISSING_... && !DPP_VISUAL_TOOL_NAME_V41(v)`，`k` 包含它，`y.visualToolAbsent331045` 记录；`shouldStopAfterTurn` 最优先：`if(DPPVisualToolAbsent331045){oe=!0,se=DPP_VISUAL_TOOL_ABSENT_331045(d);return q('visual_tool_absent_331045',!0)}`，明确告知“当前目录未暴露 read_image（tools:9），请检查 Bridge 健康并刷新工具（GET_TOOL_DESCRIPTORS 应为 24）”，停止空转。

- **B3** 新增 `DPP_VISUAL_TOOL_ABSENT_331045(locale)` 中英文提示（`zh` / `en`），放在 `/* DPP_VISUAL_WORKFLOW_V8_END */` 前。

- **C** `manifest.json` `host_permissions` 新增 `https://unlimited-underline-lunchroom.ngrok-free.dev/*`，确保 Bridge 域名有权限（此前仅依赖 `<all_urls>`? 现显式加入）。

- **D** `dspp-bare-tool-tag-v41-selftest.js` 背景 pin 更新为新 `background.js` SHA `58a7affa...`；`dspp-visual-workflow-v8-selftest.js` 增加 v41 块以包含 `DPP_VISUAL_TOOL_NAME_V41`，`v` 注入 `mcp_t_shuncode_bridge_read_image` 以复现 `visual_preflight`。

**不触碰任何授权检查**（`wN/TN/EN/DN/aI/DPP_ASSERT_CURRENT_UPLOAD_V7/DPP_DISPATCH_UPLOAD_V7` 与 `xN` allowlist 均 `gate_functions_unchanged` / `allowlist_unchanged`；`no_new_runtime_permissions` 仅 host_permissions 新增 ngrok，permissions 不变）。

## 验证

- 离线：`tools/validate-fix331045.py` **passed: true**（31 checks / 77 test processes / 61 suites，零 FAIL）。新专项：
  - `dspp-mcp-cache-v45-selftest.js`：Vc 排除 limits/timeouts、Sc 自动 ju、Nu 自愈、UPDATE 刷新、旧 Vc 已消失。
  - `dspp-visual-absent-v45-selftest.js`：`DPPVisualToolAbsent` / `DPP_VISUAL_TOOL_ABSENT` / `visual_tool_absent_331045` 存在、守卫 `!!DPP_VISUAL_TOOL_NAME_V41(v)` 存在、旧 visual missing 已消失。
  - `dspp-visual-workflow-v8-selftest.js` 已更新 v41 依赖，48/48 通过。
- 篡改源锁 / 篡改基线 / 重复打补丁均 **fail-closed**；独立重建两次一致；live 61/61。
- 浏览器：**待验收**。判据：Agent 路径 `dpp_web_response_diag_331015` 行 `descriptorCount=24`（9 内置 + 15 ShunCode），`descriptorNames[9:12]=apply_patch, find_files, read_files`（服务器原序），无 `local:mcp_capability`；若仍出现 `tools:9`，应出现 `visual_tool_absent_331045` 明确终局而非空转；`dpp_mw_bridge_diag_v10` 中 `tools:24` 应持续，`maxResultBytes` 变更不应触发 `tools:9`。

## 构建

```
python tools/apply-fix331045.py --build <干净 .36 树> <新目录>
python tools/validate-fix331045.py --root <候选> --baseline <干净 .36 树> --output <新目录>
```
链式 .36 → … → .44 → .45；源哈希锁 `tools/fix331045-source-sha256.json`（`apply-fix331044.py` + `dspp-exposure-builtin-v44-selftest.js`）。

## 升级

1. 下载 `DeepSeekPP-1.14.0-ShunCode-MCP-Fix3.3.10.45.zip`（13,984,236 B，233 文件，SHA-256 `b9e3e486815a23cd0c151b5a80cbcfaca948d4e37c2749592b3a44775aefda4b`），备份后覆盖 `D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3`。
2. `edge://extensions` 重新加载 → **彻底关闭旧 DeepSeek 标签** → 新会话。
3. 若曾改过 `Max Result Bytes`，确认 Bridge 页面已点保存；若出现 `tools:9`，在扩展侧 `ShunCode Bridge` 面板点“刷新工具”或重载扩展。
4. 回退点（本机）：`D:/tmp/DeepSeekPP-Fix331044-pre331045-20260918`（.44 冻结版，219 文件）。

## 已知观察

- `.44` 的 `dpp_web_response_diag_331015` 曾出现 2 行 `descriptorCount 9`（已归因并修复）。
- `.44` 的 `dpp_request_preflight_diag_331018` 29 行、`dpp_agent_turn_diag_331021` 11 行、`dpp_agent_tool_shape_diag` 0 行，均为 tools:9 期间的正常记录。
- `to`/`ro`（MAIN-world fetch/XHR 钩子）均保证 `U.onRequestTerminal`，`content.js` `REQUEST_TERMINAL` 均 `DPP_RECORD_WEB_DIAG_331015`，诊断链已验证。

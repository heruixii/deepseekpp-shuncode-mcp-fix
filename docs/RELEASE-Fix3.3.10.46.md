> **历史记录补注（2026-09-18）：** 相关修复与后续整改已整合入 [Fix .48](RELEASE-Fix3.3.10.48.md)。下文“未提交/未发布”等描述为当时状态，原始审计证据与不确定性保留。

# Fix 3.3.10.46（扩展版本 1.14.0.51）

2026-09-18：修复 .45 的缓存刷新运行时错误导致 DeepSeek 网页端完全不注入 MCP 工具。

## 状态

- 用户已授权修复；本机 live 已部署并完成离线验证。
- 浏览器重载后的新会话验收待用户执行，未宣称网页端已经实测通过。
- 未生成发布 ZIP、未创建 Git tag、未提交或推送、未发布 GitHub Release。
- live：D:/learn/DeepSeekPP-1.14.0-ShunCode-MCP-Fix3。
- 回退点：D:/tmp/DeepSeekPP-Fix331045-pre331046-20260918，部署前完整备份并逐文件验证。

## 修复范围

运行时代码仅修改 background.js 的 Nu() 和 Sc()；manifest/中英文扩展名更新到 .46；调整自测版本断言与背景文件哈希，新增真实函数行为测试。content-scripts/content.js、content-scripts/main-world.js、fix3-policy.js 与 .45 逐字节一致。

### Nu：目录读取与缓存自愈

- 消除刷新后循环中的 let n 暂时性死区：旧代码先 n.some 再 let n，进入刷新分支即可能抛 ReferenceError。
- 刷新后重新读取服务器配置与缓存，统一从新快照收集描述符；不再跳过旧数组里存在的 serverId，解决过期/maxAgeMs 刷新成功后仍返回旧目录或丢失新目录的问题。
- 普通目录读取不探测禁用执行的 Shell Local，不探测 disabled 服务器。
- 单个服务器发现失败不再使健康服务器工具丢失；已过期且刷新失败的 enabled 服务器不继续暴露过期描述符。
- 刷新期间被禁用或删除的服务器不会进入可执行工具列表；allowlist、执行模式仍由现有 Ho() 处理，按 descriptor.id 去重。
- includeDisabled 用于诊断展示时仍保留禁用描述符的 execution.enabled=false，不放宽执行权限。

### Sc：配置变更后的失效处理

复核时发现 .45 的第二处变量遮蔽：外层失效集合 a 被回调里的 patch 对象 a 遮蔽，连接/凭据变更分支执行 a.add 时会抛 TypeError。新实现使用明确命名，事务内更新配置及清除受影响缓存，事务外等待 enabled 服务器重新发现。limits/timeouts 变更仍不清缓存；发现失败不会撤销已保存配置。

## 验证

- 新专项 tools/dspp-mcp-cache-v46-selftest.js：抽取真实 Nu/Sc/Ho 执行，18/18 通过；同一套测试在旧 .45 上 4 通过 / 14 失败。
- tools/validate-fix331046.py：12 个结构/完整性检查、72 个验证进程、62 套自测全部通过。
- 独立重建 234 个文件全量字节一致。
- 授权函数、上传授权边界、runtime allowlist、manifest 的所有非版本字段与 .45 保持一致。
- 源篡改、基线篡改、重复输出三项 fail-closed 均验证通过。
- 部署只更新经校验的 36 个变更文件（含自测），其余 live 文件不覆盖；部署后 live 62/62 套件通过。
- 浏览器验收未完成；上述测试是离线函数与回归测试，不包含真实网页新一轮 Agent 执行。

## 文件哈希

| 文件 | SHA-256 |
|---|---|
| background.js | 22e7687c843bea404d53457cf5a44533dd29e9c062bb33f991b1480e97d9a74d |
| content-scripts/content.js（未改） | a9b317dbf6d6ddaa7b0383906a803187ad579d102242d5606bc02a38a4afede5 |
| content-scripts/main-world.js（未改） | e63b16762734e524af680e9f4e40fc18e92990f2f26afecca60f98bf3a199d92 |
| fix3-policy.js（未改） | 39915841f22a165e1cc395e17d4fdff5651050c2d70c2e3bc6291ac3b26f38c5 |

## 构建与复现

```bash
python tools/apply-fix331046.py --build D:/tmp/deepseekpp-base36 <全新候选目录>
python tools/validate-fix331046.py --root <候选目录> --baseline D:/tmp/deepseekpp-base36 --output <全新验证目录>
node tools/dspp-mcp-cache-v46-selftest.js <候选目录>
```

源锁：tools/fix331046-source-sha256.json。修复函数源：tools/dspp-cache-nu-v46.js、tools/dspp-cache-sc-v46.js。旧 builder 未改，链式 .36 → … → .45 → .46。

本机验证回执：D:/tmp/deepseekpp-fix331046-validation-20260918/report.json；安全测试与部署回执：D:/tmp/deepseekpp-fix331046-safety-20260918/report.json、deployment.json。探针、日志、私有快照不加入公开仓库。

## 浏览器验收

1. edge://extensions 重新加载 DeepSeek++，确认 1.14.0.51 / Fix 3.3.10.46。
2. 关闭旧 DeepSeek 标签，再打开新页面、新会话。
3. 先发送低成本只读任务：“调用 MCP 列出当前工作区根目录，不修改任何文件。”
4. 需看到真实 list_directory 执行成功；日志应有 content_auth1_done 与请求增强完成，不再 content_augment_error 后裸请求发送。
5. 工具数应匹配扩展实际发现清单：若仍为 15 MCP + 9 内置则 24，不硬编码未来的服务器工具数。
6. 等缓存 TTL 到期（默认约 5 分钟）后，再做一次只读任务，验证到期刷新分支。
7. 基础调用通过后再验收 read_image 及复杂任务。09:59 的 generation_err / 工具意图空转是另一个现场阶段，不因本次修复就认定所有上游生成问题已消失。

原始诊断：docs/mcp-deepseekpp-fix45-no-tools-20260918.md；前版：docs/RELEASE-Fix3.3.10.45.md。

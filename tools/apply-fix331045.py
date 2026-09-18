#!/usr/bin/env python3
"""Hash-locked .36 -> .45 builder (chains .44). Only --build BASE_36 NEW_OUTPUT.

Field evidence: .44 first run 2026-09-18 08:42-08:53, snapshot edsnap-331044-verify-20260918-0941.
A  background.js Vc() included timeouts+limits in JSON.stringify, so changing maxResultBytes
   128k->7M at 08:43:13 triggered Bc() true -> Sc() cleared toolCaches (status unknown/null/null)
   without ju(). Nu() GET_TOOL_DESCRIPTORS then returned 9 local only, no self-heal.
   Result descriptorCount 9 = DPP_CORE_TOOL_FLOOR_331033 1000, missing read_image.
B  content.js visual loop: c70e6eb6 loopId visual_preflight_331036 -> reemit_tool_call x3 ->
   unexecuted_work_limit_331036, zero tool execs, because DPP_VISUAL_RETRY_331036 scans v for
   *_read_image -> empty when tools:9, and DPPVisualMissing was true even when tool absent.
.45 fixes:
- Vc excludes limits/timeouts (only transport+headers+secrets matter for cache invalidation)
- Sc auto ju() for cleared enabled ids
- Nu self-heal: if enabled server has no cache or expired, ju() then re-collect
- UPDATE_MCP_SERVER handler triggers refreshMcpServerDiscovery
- content.js DPPVisualMissing guarded by !!DPP_VISUAL_TOOL_NAME_V41(v), plus visual_tool_absent_331045 final
- manifest host_permissions adds ngrok URL
- v41 selftest pin updated to new background.js sha
No auth check touched. main-world.js byte-identical to .43/.44.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import hashlib

HERE = Path(__file__).resolve().parent
VERSION = '1.14.0.50'
NAME = '1.14.0 ShunCode MCP Fix 3.3.10.45'

spec = importlib.util.spec_from_file_location('builder44', HERE / 'apply-fix331044.py')
B44 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B44)
sha, once = B44.sha, B44.once

# ---- background.js fixes ----
OLD_VC = "function Vc(e){return JSON.stringify({transport:{kind:e.transport.kind,url:e.transport.url??``,nativeHost:e.transport.nativeHost??``,command:e.transport.command??``,args:e.transport.args??[],cwd:e.transport.cwd??``,env:Hc(e.transport.env)},headers:e.headers,secrets:e.secrets.map(e=>({kind:e.kind,headerName:e.headerName??``,username:e.username??``,value:e.value})),timeouts:e.timeouts,limits:e.limits})}"
NEW_VC = "function Vc(e){return JSON.stringify({transport:{kind:e.transport.kind,url:e.transport.url??``,nativeHost:e.transport.nativeHost??``,command:e.transport.command??``,args:e.transport.args??[],cwd:e.transport.cwd??``,env:Hc(e.transport.env)},headers:e.headers,secrets:e.secrets.map(e=>({kind:e.kind,headerName:e.headerName??``,username:e.username??``,value:e.value}))})}"

OLD_SC = "async function Sc(e,t){return _c.run(async()=>{let n=await kc(),r=null,i=new Set,a=n.servers.map(n=>{if(n.id!==e)return n;let a=t.secrets?{...t,secrets:Lc(n.secrets,t.secrets)}:t,o=jc({...n,...a,updatedAt:Date.now(),status:Mc(n,a)});return Bc(n,o)?(i.add(n.id),r={...o,status:o.enabled?`unknown`:`disabled`,lastConnectedAt:null,lastError:null},r):(r=o,r)});return r?(await Ac({...n,servers:a,toolCaches:i.size>0?n.toolCaches.filter(e=>!i.has(e.serverId)):n.toolCaches}),Dc(r)):null})}"
NEW_SC = "async function Sc(e,t){let n=new Set;let r=await _c.run(async()=>{let r=await kc(),i=null,a=new Set,o=r.servers.map(r=>{if(r.id!==e)return r;let a=t.secrets?{...t,secrets:Lc(r.secrets,t.secrets)}:t,s=jc({...r,...a,updatedAt:Date.now(),status:Mc(r,a)});return Bc(r,s)?(a.add(r.id),i={...s,status:s.enabled?`unknown`:`disabled`,lastConnectedAt:null,lastError:null},i):(i=s,i)});return n=a,i?(await Ac({...r,servers:o,toolCaches:a.size>0?r.toolCaches.filter(e=>!a.has(e.serverId)):r.toolCaches}),Dc(i)):null});if(n&&n.size>0)for(let e of n)ju(e).catch(()=>{});return r}"

OLD_NU = "async function Nu(e){let[t,n]=await Promise.all([yc({includeSecrets:!1}),Tc()]),r=Date.now(),i=new Map(t.map(e=>[e.id,e])),a=[];for(let t of n){let n=i.get(t.serverId);if(!n||!e?.includeDisabled&&!n.enabled||e?.maxAgeMs!=null&&r-t.refreshedAt>e.maxAgeMs)continue;let o=Ho(t.descriptors,n);a.push(...o.filter(t=>e?.includeDisabled||t.execution.enabled&&t.execution.mode!==`disabled`))}return a}"
NEW_NU = "async function Nu(e){let[t,n]=await Promise.all([yc({includeSecrets:!1}),Tc()]),r=Date.now(),i=new Map(t.map(e=>[e.id,e])),a=[],o=new Set;for(let s of n){let n=i.get(s.serverId);if(!n||!e?.includeDisabled&&!n.enabled||e?.maxAgeMs!=null&&r-s.refreshedAt>e.maxAgeMs)continue;let c=Ho(s.descriptors,n);a.push(...c.filter(t=>e?.includeDisabled||t.execution.enabled&&t.execution.mode!==`disabled`))}for(let s of t){if(!e?.includeDisabled&&!s.enabled)continue;let c=n.find(e=>e.serverId===s.id);if(!c||(e?.maxAgeMs!=null&&r-c.refreshedAt>e.maxAgeMs)||c.expiresAt<=r)o.add(s.id)}if(o.size>0){await Promise.all([...o].map(e=>ju(e).catch(()=>{})));let c=await Tc();for(let t of c){if(n.some(e=>e.serverId===t.serverId))continue;let n=i.get(t.serverId);if(!n||!e?.includeDisabled&&!n.enabled)continue;let r=Ho(t.descriptors,n);a.push(...r.filter(t=>e?.includeDisabled||t.execution.enabled&&t.execution.mode!==`disabled`))}}return a}"

OLD_UPDATE = "Y(`UPDATE_MCP_SERVER`,async(n,r)=>{let i=await e.updateMcpServer(n.id,n.patch);return await t(r.tabId),i})"
NEW_UPDATE = "Y(`UPDATE_MCP_SERVER`,async(n,r)=>{let i=await e.updateMcpServer(n.id,n.patch);if(i){try{await e.refreshMcpServerDiscovery(n.id)}catch{}}return await t(r.tabId),i})"

# ---- content.js fixes ----
OLD_VISUAL_MISSING = "DPPVisualMissing331036=!r&&DPP_VISUAL_MISSING_331036(t.originalPrompt,g,p),k=!!DPPUnregTag331033||DPPVisualMissing331036||DPP_TOOL_INTENT_331021(n,te);"
NEW_VISUAL_MISSING = "DPPVisualMissing331036=!r&&DPP_VISUAL_MISSING_331036(t.originalPrompt,g,p)&&!!DPP_VISUAL_TOOL_NAME_V41(v),DPPVisualToolAbsent331045=!r&&DPP_VISUAL_MISSING_331036(t.originalPrompt,g,p)&&!DPP_VISUAL_TOOL_NAME_V41(v),k=!!DPPUnregTag331033||DPPVisualMissing331036||DPPVisualToolAbsent331045||DPP_TOOL_INTENT_331021(n,te);"

OLD_VISUAL_MISSING2 = "y.visualMissing=DPPVisualMissing331036;"
NEW_VISUAL_MISSING2 = "y.visualMissing=DPPVisualMissing331036;y.visualToolAbsent331045=DPPVisualToolAbsent331045;"

OLD_VISUAL_HANDLER = "if(DPPUnregTag331033||DPPVisualMissing331036){if(y.count>=Ce.maxNudges||y.currentTurnIsNudge&&y.toolIntentNudgesInStep>=DPP_TOOL_INTENT_NUDGE_MAX_331021)"
NEW_VISUAL_HANDLER = "if(DPPVisualToolAbsent331045){oe=!0,se=DPP_VISUAL_TOOL_ABSENT_331045(d);return q(`visual_tool_absent_331045`,!0)}if(DPPUnregTag331033||DPPVisualMissing331036){if(y.count>=Ce.maxNudges||y.currentTurnIsNudge&&y.toolIntentNudgesInStep>=DPP_TOOL_INTENT_NUDGE_MAX_331021)"

OLD_WORKFLOW_END = "/* DPP_VISUAL_WORKFLOW_V8_END */"
NEW_WORKFLOW_END = "function DPP_VISUAL_TOOL_ABSENT_331045(locale){return String(locale||'').toLowerCase().startsWith('zh')?'[Fix 3.3.10.45 \\u89c6\\u89c9\\u5de5\\u5177\\u7f3a\\u5931] \\u5f53\\u524d\\u76ee\\u5f55\\u672a\\u66b4\\u9732 read_image \\u5de5\\u5177\\uff08tools:9\\uff09\\uff0c\\u65e0\\u6cd5\\u5b8c\\u6210\\u201c\\u6309\\u53c2\\u8003\\u56fe\\u4f5c\\u753b\\u201d\\u7c7b\\u4efb\\u52a1\\u3002\\u8bf7\\u5148\\u5728 ShunCode Bridge \\u4e2d\\u68c0\\u67e5 MCP \\u670d\\u52a1\\u72b6\\u6001\\u5e76\\u5237\\u65b0\\u5de5\\u5177\\uff08GET_TOOL_DESCRIPTORS \\u5e94\\u4e3a 24\\uff09\\uff0c\\u6216\\u91cd\\u65b0\\u52a0\\u8f7d\\u6269\\u5c55\\u540e\\u91cd\\u8bd5\\uff1b\\u5df2\\u505c\\u6b62\\u7a7a\\u8f6c\\u7684\\u91cd\\u8bd5\\u3002':'[Fix 3.3.10.45 visual tool absent] The current catalogue does not expose read_image (tools:9), so the explicit local-reference task cannot proceed. Please check the ShunCode Bridge MCP server health and refresh tools (GET_TOOL_DESCRIPTORS should be 24), or reload the extension and retry; stopped the empty retry loop.'}\n/* DPP_VISUAL_WORKFLOW_V8_END */"

CONTENT_EDITS = [
    (OLD_VISUAL_MISSING, NEW_VISUAL_MISSING),
    (OLD_VISUAL_MISSING2, NEW_VISUAL_MISSING2),
    (OLD_VISUAL_HANDLER, NEW_VISUAL_HANDLER),
    (OLD_WORKFLOW_END, NEW_WORKFLOW_END),
]

BG_EDITS = [
    (OLD_VC, NEW_VC),
    (OLD_SC, NEW_SC),
    (OLD_NU, NEW_NU),
    (OLD_UPDATE, NEW_UPDATE),
]

def gates(text):
    return (text.replace('1.14.0.49', VERSION)
            .replace('1.14.0 ShunCode MCP Fix 3.3.10.44', NAME)
            .replace('manifest version_name is Fix 3.3.10.44', 'manifest version_name is Fix 3.3.10.45')
            .replace('|36|37|38|39|40|41|42|43|44)$', '|36|37|38|39|40|41|42|43|44|45)$'))

def build(base, output):
    base = Path(base).resolve()
    output = Path(output).resolve()
    if output.exists() or output == base or base in output.parents:
        raise ValueError('Output must be new and outside baseline')
    staging = output.parent / (output.name + '.stage44')
    if staging.exists():
        raise ValueError('Staging path already exists: ' + str(staging))
    locks = json.loads((HERE / 'fix331045-source-sha256.json').read_text(encoding='utf-8'))
    for n in ['apply-fix331044.py', 'dspp-exposure-builtin-v44-selftest.js']:
        if sha((HERE / n).read_bytes()) != locks[n]:
            raise ValueError('Source hash mismatch: ' + n)
    values = B44.build(str(base), str(staging))
    enc = lambda s: s.encode('utf-8') if isinstance(s, str) else s
    bg = values['background.js']
    if b'331045' in bg:
        raise ValueError('v45 background change already present')
    for o, n in BG_EDITS:
        bg = once(bg, enc(o), enc(n))
    values['background.js'] = bg
    c = values['content-scripts/content.js']
    if b'331045' in c:
        raise ValueError('v45 content change already present')
    for o, n in CONTENT_EDITS:
        c = once(c, enc(o), enc(n))
    values['content-scripts/content.js'] = c
    for n in ['background.js', 'content-scripts/content.js', 'content-scripts/main-world.js']:
        result = subprocess.run(['node', '--check', '--input-type=module'], input=values[n], capture_output=True)
        if result.returncode:
            raise ValueError('Node syntax failure: ' + n + ' ' + result.stderr.decode('utf-8', 'replace')[:800])
    result = subprocess.run(['node', '--check'], input=values['fix3-policy.js'], capture_output=True)
    if result.returncode:
        raise ValueError('Node syntax failure: fix3-policy.js ' + result.stderr.decode('utf-8', 'replace')[:800])
    mf_raw = values['manifest.json'].decode('utf-8')
    mf_json = json.loads(mf_raw)
    mf_json['version'] = VERSION
    mf_json['version_name'] = NAME
    hp = mf_json.get('host_permissions', [])
    ngrok = 'https://unlimited-underline-lunchroom.ngrok-free.dev/*'
    if ngrok not in hp:
        hp.append(ngrok)
    mf_json['host_permissions'] = hp
    values['manifest.json'] = json.dumps(mf_json, indent=2, ensure_ascii=False).encode('utf-8') + b'\n'
    for lang in ['en', 'zh_CN']:
        n = '_locales/' + lang + '/messages.json'
        values[n] = once(values[n], 'DeepSeek++ ShunCode MCP Fix 3.3.10.44', 'DeepSeek++ ShunCode MCP Fix 3.3.10.45')
    for n in list(values):
        if '/' not in n and 'selftest' in n and n.endswith('.js'):
            values[n] = gates(values[n].decode('utf-8')).encode('utf-8')
    bg_sha = sha(values['background.js'])
    v41_name = 'dspp-bare-tool-tag-v41-selftest.js'
    v41 = values[v41_name].decode('utf-8')
    v41 = re.sub(r"bgSha === '[0-9a-f]{64}'", f"bgSha === '{bg_sha}'", v41)
    values[v41_name] = v41.encode('utf-8')
    v45_mcp = (HERE / 'dspp-mcp-cache-v45-selftest.js').read_bytes() if (HERE / 'dspp-mcp-cache-v45-selftest.js').exists() else None
    if v45_mcp:
        txt = v45_mcp.decode('utf-8')
        txt = gates(txt)
        txt = txt.replace('76df1046a8bd3247484dc96092785b876b7b7985cbfe31c5cd31947212a536f5', bg_sha)
        values['dspp-mcp-cache-v45-selftest.js'] = txt.encode('utf-8')
    v45_vis = (HERE / 'dspp-visual-absent-v45-selftest.js').read_bytes() if (HERE / 'dspp-visual-absent-v45-selftest.js').exists() else None
    if v45_vis:
        txt = v45_vis.decode('utf-8')
        txt = gates(txt)
        values['dspp-visual-absent-v45-selftest.js'] = txt.encode('utf-8')
    output.mkdir(parents=True)
    for n, raw in values.items():
        p = output / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    shutil.rmtree(staging)
    print(json.dumps({'version': VERSION, 'files': len(values),
                      'background_sha256': sha(values['background.js']),
                      'content_sha256': sha(values['content-scripts/content.js']),
                      'policy_sha256': sha(values['fix3-policy.js']),
                      'main_world_sha256': sha(values['content-scripts/main-world.js'])}, indent=2))
    return values

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', nargs=2, metavar=('BASE_36', 'NEW_OUTPUT'), required=True)
    args = ap.parse_args()
    try:
        build(*args.build)
    except (ValueError, OSError) as e:
        raise SystemExit('FAIL-CLOSED: ' + str(e))

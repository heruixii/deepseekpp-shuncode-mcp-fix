from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
targets=['content-scripts/content.js','manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json']
expected={
 'content-scripts/content.js':'3D7F94F18D0ECD8BA4B19C76416586C1B7A2E8A66AB685DF239393B7C600F794',
 'manifest.json':'18F97B8D2A81A100F6729B55B319A3A0C8F97972246F7D024CA8932D6A075E6C',
 '_locales/en/messages.json':'B614DEC8928A5DA1C099C7F5685EBB97078C82D4BB2A67142518B2E3D31EAC60',
 '_locales/zh_CN/messages.json':'BB986E53411BD5E6006FA6C6EBC1AE78662536CFD4DAF6D28A714EC20C0B0590'}
output_expected={
 'content-scripts/content.js':'7A2DB7A62D041CD9C31433C9F4D419E7FBE95AEF12B37C78FE375EC8AF73A7CF',
 'manifest.json':'BEBFA1F53942AFE394BE3861A84754A0CAE9E2344BB7E1596D4C8C757A749AA5',
 '_locales/en/messages.json':'541076A6B7B717DA0507AF6A90F1865FF510809D4249044D6CEF9BDBEB271CCB',
 '_locales/zh_CN/messages.json':'93D7F7C3DC28429FE8AAB33BDCDE9594647496E4B35702E1304AB4EAD70963C2'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest=root/'manifest.json'
try: m=json.loads(manifest.read_text(encoding='utf-8-sig'))
except Exception as e: raise SystemExit(f'APPLY_FIX33107_FAIL: manifest unreadable: {e}')
content=root/'content-scripts/content.js'
if m.get('version')=='1.14.0.12' and m.get('version_name')=='1.14.0 ShunCode MCP Fix 3.3.10.7' and content.exists() and 'DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107' in content.read_text(encoding='utf-8-sig'):
 print('APPLY_FIX33107_ALREADY_APPLIED'); raise SystemExit(0)
for rel in targets:
 p=root/rel
 if not p.is_file(): raise SystemExit(f'APPLY_FIX33107_FAIL: missing {rel}')
 got=sha(p)
 if got!=expected[rel]: raise SystemExit(f'APPLY_FIX33107_FAIL: hash mismatch {rel} expected={expected[rel]} got={got}')
s=content.read_text(encoding='utf-8-sig')
old='function DPP_SHOULD_DIRECT_RETRY_33(e,t,n){return DPP_TOOL_NAME_33(e)===`run_command`&&t?.background!==!0&&String(t?.execution??`pty`).toLowerCase()!==`direct`&&DPP_TOOL_EFFECT_31(`run_command`,t)===`verification`&&DPP_PTY_EMPTY_33(n)}function Uz(e,t,d){'
new='function DPP_SHOULD_DIRECT_RETRY_33(e,t,n){return DPP_TOOL_NAME_33(e)===`run_command`&&t?.background!==!0&&String(t?.execution??`pty`).toLowerCase()!==`direct`&&DPP_TOOL_EFFECT_31(`run_command`,t)===`verification`&&DPP_PTY_EMPTY_33(n)}function DPP_MCP_TRANSIENT_VERIFICATION_33107(e,t,n){let r=String(n?.error?.code??``),i=String(n?.error?.message??``);return n?.ok===!1&&n?.error?.retryable===!0&&DPP_TOOL_EFFECT_31(e,t)===`verification`&&r===`mcp_http_error`&&/\\bHTTP\\s+(?:502|503|504)\\b/i.test(i)}function DPP_MCP_RETRY_DELAY_33107(e,t=850){if(e?.aborted)return Promise.resolve(!1);return new Promise(n=>{let r=null,i=!1,a=o=>{if(i)return;i=!0,r!==null&&clearTimeout(r),e?.removeEventListener?.(`abort`,s),n(o)},s=()=>a(!1);e?.addEventListener?.(`abort`,s,{once:!0}),r=setTimeout(()=>a(!0),t)})}function Uz(e,t,d){'
if s.count(old)!=1: raise SystemExit(f'APPLY_FIX33107_FAIL: helper anchor count={s.count(old)}')
s=s.replace(old,new,1)
old='let f=await n({id:t,name:e.name,invocationName:e.invocationName,payload:c,raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});if(DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)){'
new='let f=await n({id:t,name:e.name,invocationName:e.invocationName,payload:c,raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});if(DPP_MCP_TRANSIENT_VERIFICATION_33107(e.invocationName,c,f?.result)&&await DPP_MCP_RETRY_DELAY_33107(a)){let i=await n({id:`${t}:dpp33107-mcp-retry`,name:e.name,invocationName:e.invocationName,payload:c,raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});f=i}if(DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)){'
if s.count(old)!=1: raise SystemExit(f'APPLY_FIX33107_FAIL: retry anchor count={s.count(old)}')
s=s.replace(old,new,1)
old='async function bZ(e){let t=typeof e.id==`string`?e.id:``,n=typeof e.requestId==`string`?e.requestId:``;if(!t)return;let r=null,i=``,a=!1;try{'
new='function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;return r1(),!0}async function bZ(e){let t=typeof e.id==`string`?e.id:``,n=typeof e.requestId==`string`?e.requestId:``;if(!t)return;let r=null,i=``,a=!1;try{'
if s.count(old)!=1: raise SystemExit(f'APPLY_FIX33107_FAIL: lifecycle helper anchor count={s.count(old)}')
s=s.replace(old,new,1)
old='let o=Kc(e.route,e.body);if(!o){xZ(t);return}let s=o.route===`regenerate`?await wZ(o.body):null;'
new='let o=Kc(e.route,e.body);if(!o){xZ(t);return}DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107();let s=o.route===`regenerate`?await wZ(o.body):null;'
if s.count(old)!=1: raise SystemExit(f'APPLY_FIX33107_FAIL: request hook anchor count={s.count(old)}')
s=s.replace(old,new,1)
updates={'content-scripts/content.js':s.encode('utf-8')}
m['version']='1.14.0.12';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.7'
updates['manifest.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')
for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
 d=json.loads((root/rel).read_text(encoding='utf-8-sig'))
 d['extension_name']['message']='DeepSeek++ ShunCode MCP Fix 3.3.10.7'
 updates[rel]=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')
for rel,data in updates.items():
 got=hashlib.sha256(data).hexdigest().upper()
 if got!=output_expected[rel]: raise SystemExit(f'APPLY_FIX33107_FAIL: output hash mismatch {rel} expected={output_expected[rel]} got={got}')
for rel,data in updates.items(): (root/rel).write_bytes(data)
print('APPLY_FIX33107_PASS')

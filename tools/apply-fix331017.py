from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
EXPECTED={'content-scripts/content.js': '7FECC173832CE58B39DCB118537CD2B42D70418418D51C0C5EC2B81EB9CB071E', 'content-scripts/main-world.js': 'E1238231B0B4C70B3C1DDC6B5821B9DF69AB684FA1829D14934DA23337D68C8C', 'manifest.json': 'C22AFE084F513B9A44155CCC94D4F67EC4717B3EEEE28694F06A8E338160F4C4', '_locales/en/messages.json': '177059BA9CA77B52235712F0A635FD02E54C13B1D8F00404D8B5AE017C70CE4F', '_locales/zh_CN/messages.json': '5A8876A0E030E2F061A4C8EF74EB6CEC99B145BE4A2618D7EC548677DF6C2B47'}
OUTPUT_EXPECTED={'content-scripts/content.js': '592F3B0A797A4B26AF613B63CD3787555FAD90B1F6D04588C49FBDFC7C9EA4C4', 'content-scripts/main-world.js': '75B63C0A0921C7C7CB955E8A518DCDE2C2E59CF4923F11CDE1D1505C71A6C639', 'manifest.json': '76672787E161EA974397547E3A54E985F64B8EB11EBB532158DF31A2485865DC', '_locales/en/messages.json': '5EFC76BB6FAB208B2E3D3201BCCBF112D731592DD63FB36ABDBE20DE50A3FA55', '_locales/zh_CN/messages.json': 'C9C4BE0ED306EF099B3BE4095C530E3B10D2838E89284CC882E6C3FA6BEBFCF3'}
OLD_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.16'
NEW_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.17'
OLD_MANIFEST_VERSION='1.14.0.21'
NEW_MANIFEST_VERSION='1.14.0.22'
OLD_UI='function ui(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1}}'
NEW_UI='function ui(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,controlTrail:[]}}'
OLD_HI='function hi(e,t,n,r,i){zi(e,n),r.onParsed?.(e,t);let a=Oi(e,wi(n));'
NEW_HI='function DPP_CONTROL_VALUE_331017(e){if(typeof e==`number`&&Number.isFinite(e)||typeof e==`boolean`)return e;if(typeof e==`string`){let t=e.trim();return t&&t.length<=80?t:null}return null}function DPP_CAPTURE_SSE_CONTROL_331017(e,t,n){let r=n?.controlTrail;if(!Array.isArray(r)||!e||typeof e!=`object`)return;let i=0,a=(e,n,o=0)=>{if(i>=48||o>5||!e||typeof e!=`object`)return;if(i++,Array.isArray(e)){for(let t of e){if(i>=48)break;a(t,n,o+1)}return}let s=typeof e.p==`string`?e.p:null,c=typeof e.o==`string`?e.o:null,l=(e,n)=>{if(typeof e!=`string`||!/(?:status|code|error|finish|quasi)/i.test(e))return;let i=e.toLowerCase(),a={path:e.slice(0,120)};c&&(a.op=c.slice(0,32)),typeof t==`string`&&t&&(a.event=t.slice(0,32));let o=/(?:status|code|finish|quasi)/i.test(i)?DPP_CONTROL_VALUE_331017(n):null;o!==null&&(a.value=typeof o==`string`?o.slice(0,80):o),/error/i.test(i)&&(a.errorPresent=!0),r.push(a),r.length>8&&r.splice(0,r.length-8)};s&&l(s,e.v);for(let t of [`status`,`code`,`error_code`,`errorCode`,`finish_reason`,`quasi_status`])t in e&&l((n?`${n}/`:``)+t,e[t]);e.o===`BATCH`&&Array.isArray(e.v)?a(e.v,s??n,o+1):e.v&&typeof e.v==`object`&&!Array.isArray(e.v)&&a(e.v,s??n,o+1),e.error&&typeof e.error==`object`&&a(e.error,(n?`${n}/`:``)+`error`,o+1)};a(e,``,0)}function hi(e,t,n,r,i){zi(e,n),DPP_CAPTURE_SSE_CONTROL_331017(e,t,n),r.onParsed?.(e,t);let a=Oi(e,wi(n));'
OLD_FINISH='dppStreamFinished331015:n.finished===!0,dppRecoveredDsml331015:DPPRecoveredDsml,dppVisibleChars331015:o.getVisibleText().length}'
NEW_FINISH='dppStreamFinished331015:n.finished===!0,dppRecoveredDsml331015:DPPRecoveredDsml,dppVisibleChars331015:o.getVisibleText().length,dppControlTrail331017:Array.isArray(n.controlTrail)?n.controlTrail.slice(-8):[]}'
OLD_FETCH='visibleChars:a?.dppVisibleChars331015??0})'
NEW_FETCH='visibleChars:a?.dppVisibleChars331015??0,controlTrail:a?.dppControlTrail331017??[]})'
OLD_XHR='visibleChars:s?.dppVisibleChars331015??0})'
NEW_XHR='visibleChars:s?.dppVisibleChars331015??0,controlTrail:s?.dppControlTrail331017??[]})'
OLD_PERSIST='visibleChars:i(t.visibleChars),errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``,errorMessage:typeof t.errorMessage==`string`?t.errorMessage.slice(0,300):``}'
NEW_PERSIST='visibleChars:i(t.visibleChars),controlTrail:Array.isArray(t.controlTrail)?t.controlTrail.slice(-8).map(e=>{let t={};return typeof e?.path==`string`&&(t.path=e.path.slice(0,120)),typeof e?.op==`string`&&(t.op=e.op.slice(0,32)),typeof e?.event==`string`&&(t.event=e.event.slice(0,32)),typeof e?.errorPresent==`boolean`&&(t.errorPresent=e.errorPresent),(typeof e?.value==`number`&&Number.isFinite(e.value)||typeof e?.value==`boolean`)&&(t.value=e.value),typeof e?.value==`string`&&e.value.length<=80&&(t.value=e.value),t}).filter(e=>typeof e.path==`string`):[],errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``,errorMessage:typeof t.errorMessage==`string`?t.errorMessage.slice(0,300):``}'
def sha(data): return hashlib.sha256(data).hexdigest().upper()
def crlf(text): return text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8')
def main(arg):
 root=Path(arg).resolve(); p={k:root/k for k in EXPECTED}
 m=json.loads(p['manifest.json'].read_text(encoding='utf-8-sig')); mw=p['content-scripts/main-world.js'].read_text(encoding='utf-8-sig')
 if m.get('version')==NEW_MANIFEST_VERSION and m.get('version_name')==NEW_VERSION and 'DPP_CAPTURE_SSE_CONTROL_331017' in mw:
  [(_ for _ in ()).throw(RuntimeError(f'already-patched hash mismatch for {r}: {sha(p[r].read_bytes())}')) for r,w in OUTPUT_EXPECTED.items() if sha(p[r].read_bytes())!=w]; print('APPLY_FIX331017_OK already-applied'); return
 if m.get('version')!=OLD_MANIFEST_VERSION or m.get('version_name')!=OLD_VERSION: raise RuntimeError(f'expected {OLD_VERSION}, got {m.get("version_name")!r}')
 for r,w in EXPECTED.items():
  got=sha(p[r].read_bytes())
  if got!=w: raise RuntimeError(f'input hash mismatch for {r}: {got}')
 c=p['content-scripts/content.js'].read_text(encoding='utf-8-sig')
 for old,new,label in [(OLD_UI,NEW_UI,'ui'),(OLD_HI,NEW_HI,'capture'),(OLD_FINISH,NEW_FINISH,'finish'),(OLD_FETCH,NEW_FETCH,'fetch'),(OLD_XHR,NEW_XHR,'xhr')]:
  if mw.count(old)!=1: raise RuntimeError(f'{label} target count {mw.count(old)}')
  mw=mw.replace(old,new,1)
 if c.count(OLD_PERSIST)!=1: raise RuntimeError(f'persist target count {c.count(OLD_PERSIST)}')
 c=c.replace(OLD_PERSIST,NEW_PERSIST,1); m['version']=NEW_MANIFEST_VERSION; m['version_name']=NEW_VERSION
 out={'content-scripts/content.js':crlf(c),'content-scripts/main-world.js':crlf(mw),'manifest.json':crlf(json.dumps(m,ensure_ascii=False,indent=2)+'\n')}
 for r in ('_locales/en/messages.json','_locales/zh_CN/messages.json'):
  x=p[r].read_text(encoding='utf-8-sig')
  if 'Fix 3.3.10.16' not in x: raise RuntimeError(f'locale marker missing for {r}')
  out[r]=crlf(x.replace('Fix 3.3.10.16','Fix 3.3.10.17'))
 for r,b in out.items():
  got=sha(b)
  if got!=OUTPUT_EXPECTED[r]: raise RuntimeError(f'staged output hash mismatch for {r}: {got}')
 staged=[]
 try:
  for r,b in out.items():
   t=p[r].with_name(p[r].name+'.fix331017.tmp'); t.write_bytes(b); staged.append((t,p[r]))
  for t,d in staged: os.replace(t,d)
 finally:
  for t,_ in staged:
   if t.exists(): t.unlink()
 print('APPLY_FIX331017_OK')
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: apply-fix331017.py <extension-root>')
 main(sys.argv[1])

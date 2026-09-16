from __future__ import annotations
import hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
OLD_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.19'; NEW_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.20'
OLD_MANIFEST_VERSION='1.14.0.24'; NEW_MANIFEST_VERSION='1.14.0.25'
EXPECTED={
'content-scripts/content.js':'5161896C3E85A29EF50343FEEFD807AB464C01F46A2E7C180234EE6C6AE55856',
'content-scripts/main-world.js':'D2C47A42FE0229A406ECD674C9409F893ABD3B95D2B7D691B103059529BA0C2F',
'background.js':'809DB9658729E70744BA48D44698F531562C2E5BCB9A89D01162F1E3CC1FCA5B',
'manifest.json':'4DF630AAD42AFDB1CF493AA8E0DA2F8BC08AAFDCD57814C77F10E2EDCF516D9C',
'_locales/en/messages.json':'895A2E0A423A6253952AFCA17FAF5D842A47EB49B11372DEDC197BB1D8956111',
'_locales/zh_CN/messages.json':'33BABFE7D8A76DEBE5E44DDDCBD0BF57D0E7E2A7FCC068390357C5F54F268238'}
OUTPUT_EXPECTED={
'content-scripts/content.js':'3A054DCA651805A533D1CD2798ADAC3D1F70A25637A8D351BFC4BD48D3B917A3',
'content-scripts/main-world.js':'D3BCDE6E8F5CF1E72C79244256389E6BD6E06F58B94BFEB67558FF3881E8F0B4',
'background.js':'809DB9658729E70744BA48D44698F531562C2E5BCB9A89D01162F1E3CC1FCA5B',
'manifest.json':'31DA14C6C11EC6D33CEACB02DEE359EF190EC059CFA50599F3AA0706E3A6BC85',
'_locales/en/messages.json':'66FC13D1506A790B623464911A984CDB0747E9E6D130FF9702C2921D35CA771C',
'_locales/zh_CN/messages.json':'E0122B64A62A524BF8EBAD72FE3F6FCACEAE432BFD0E71A906DEB4BE16F61EC4'}
RELS=list(EXPECTED)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rep(s,o,n,label,count=1):
 c=s.count(o)
 if c!=count: raise RuntimeError(f'{label}: expected {count}, found {c}')
 return s.replace(o,n,count)
def wr(p,s): p.write_text(s,encoding='utf-8',newline='\r\n')
def transform_main(p):
 s=p.read_text('utf-8-sig')
 s=rep(s,'function DPP_PREFLIGHT_331018(e){try{U.onRequestPreflight(e)}catch{}}function Sa(e){','''function DPP_PREFLIGHT_331018(e){try{U.onRequestPreflight(e)}catch{}}var DPP_GENERATION_ERR_RECOVERY_331020=new Map;function DPP_RECOVERY_KEY_331020(e){let t=typeof e?.chatSessionId==`string`?e.chatSessionId:``;return t||``}function DPP_RECOVERY_MODE_331020(e){let t=DPP_RECOVERY_KEY_331020(e);if(!t)return null;let n=DPP_GENERATION_ERR_RECOVERY_331020.get(t);if(!n||n.expiresAt<=Date.now())return n&&DPP_GENERATION_ERR_RECOVERY_331020.delete(t),null;if(n.expectedParentMessageId==null||e?.parentMessageId!==n.expectedParentMessageId)return null;return DPP_GENERATION_ERR_RECOVERY_331020.delete(t),`compact`}function DPP_GENERATION_ERR_RESULT_331020(e){return e?.dppStreamFinished331015===!1&&Array.isArray(e?.dppControlTrail331017)&&e.dppControlTrail331017.some(e=>e?.path===`finish_reason`&&String(e?.value??``).toLowerCase()===`generation_err`)}function DPP_TRACK_GENERATION_RESULT_331020(e,t){let n=DPP_RECOVERY_KEY_331020(e);if(!n)return;if(DPP_GENERATION_ERR_RESULT_331020(t)&&t?.assistantMessageId!=null){let r=DPP_GENERATION_ERR_RECOVERY_331020.get(n),i=Math.min(3,(r?.failures??0)+1);DPP_GENERATION_ERR_RECOVERY_331020.set(n,{failures:i,expectedParentMessageId:t.assistantMessageId,expiresAt:Date.now()+12e3}),DPP_PREFLIGHT_331018({stage:`mw_generation_err_recovery_armed`,requestId:e?.requestId??``,chatSessionId:e?.chatSessionId??null,recoveryMode:`compact`,failureCount:i,expectedParentMessageId:t.assistantMessageId});return}t?.dppStreamFinished331015===!0&&DPP_GENERATION_ERR_RECOVERY_331020.delete(n)}function Sa(e){''','recovery helpers')
 s=rep(s,'let c=DPPInitialRequest331018,l=[...U.toolDescriptors],u=null,d=!1,DPPAugmentStart331018=performance.now();','let c=DPPInitialRequest331018,DPPRecoveryMode331020=DPP_RECOVERY_MODE_331020(c),l=[...U.toolDescriptors],u=null,d=!1,DPPAugmentStart331018=performance.now();','fetch mode')
 s=rep(s,'stage:`mw_augment_begin`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId});try{u=await U.onRequestBody(n.body,c.requestId,a),','stage:`mw_augment_begin`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId,parentMessageId:c.parentMessageId,recoveryMode:DPPRecoveryMode331020});try{u=await U.onRequestBody(n.body,c.requestId,a,DPPRecoveryMode331020),','fetch bridge')
 s=rep(s,'stage:`mw_transport_started`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,augmentedBodyChars:(u?.body??n.body).length,chatSessionId:f.chatSessionId??null}),to(','stage:`mw_transport_started`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,augmentedBodyChars:(u?.body??n.body).length,chatSessionId:f.chatSessionId??null,recoveryMode:DPPRecoveryMode331020}),to(','fetch transport')
 s=rep(s,'descriptorNames:f.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:f.chatSessionId??null}})}','descriptorNames:f.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:f.chatSessionId??null,recoveryMode:DPPRecoveryMode331020}})}','fetch diag')
 s=rep(s,'let i=DPPInitialRequest331018,o=null,DPPAugmentStart331018=performance.now();','let i=DPPInitialRequest331018,DPPRecoveryMode331020=DPP_RECOVERY_MODE_331020(i),o=null,DPPAugmentStart331018=performance.now();','xhr mode')
 s=rep(s,'stage:`mw_augment_begin`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId});try{U.onHeadersCaptured(Ea(n.get(t)));let s=[...U.toolDescriptors],c=null,l=!1;try{c=await U.onRequestBody(e,i.requestId,r),','stage:`mw_augment_begin`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId,parentMessageId:i.parentMessageId,recoveryMode:DPPRecoveryMode331020});try{U.onHeadersCaptured(Ea(n.get(t)));let s=[...U.toolDescriptors],c=null,l=!1;try{c=await U.onRequestBody(e,i.requestId,r,DPPRecoveryMode331020),','xhr bridge')
 s=rep(s,'descriptorNames:v.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:v.chatSessionId??null},o=ro(t,v)','descriptorNames:v.toolDescriptors.map(e=>e?.invocationName??e?.name).filter(e=>typeof e==`string`).slice(0,12),chatSessionId:v.chatSessionId??null,recoveryMode:DPPRecoveryMode331020},o=ro(t,v)','xhr diag')
 s=rep(s,'stage:`mw_transport_started`,requestId:i.requestId,route:r,rawBodyChars:e.length,augmentedBodyChars:u.length,chatSessionId:v.chatSessionId??null}),a.call(t,u)','stage:`mw_transport_started`,requestId:i.requestId,route:r,rawBodyChars:e.length,augmentedBodyChars:u.length,chatSessionId:v.chatSessionId??null,recoveryMode:DPPRecoveryMode331020}),a.call(t,u)','xhr transport')
 s=rep(s,'let a=u().finish(e);a&&U.onResponseComplete(a),f=!0,e.close(),r({...o,phase:`eof`','let a=u().finish(e);a&&U.onResponseComplete(a),DPP_TRACK_GENERATION_RESULT_331020(t,a),f=!0,e.close(),r({...o,phase:`eof`','fetch track')
 s=rep(s,'e.addEventListener(`load`,()=>{try{p()}finally{l({...c(),phase:`xhr_load`','e.addEventListener(`load`,()=>{try{p(),DPP_TRACK_GENERATION_RESULT_331020(t,s)}finally{l({...c(),phase:`xhr_load`','xhr track')
 s=rep(s,'AUGMENT_REQUEST_BODY:e=>Q(e.id)&&typeof e.body==`string`&&s(e.route)&&(e.requestId===void 0||Q(e.requestId)),','AUGMENT_REQUEST_BODY:e=>Q(e.id)&&typeof e.body==`string`&&s(e.route)&&(e.requestId===void 0||Q(e.requestId))&&(e.recoveryMode===void 0||e.recoveryMode===null||e.recoveryMode===`compact`),','main validator')
 s=rep(s,'requestAugmentedBody:(e,t,a)=>{if(!r?.active||!i)return Promise.resolve(null);let o=n();return new Promise(n=>{let i=r.setTimeout(()=>{u.delete(o),n(null)},hs);if(u.set(o,{resolve:n,timeout:i}),!m({type:`AUGMENT_REQUEST_BODY`,id:o,requestId:t,route:a,body:e})){let e=u.get(o);e&&(u.delete(o),r?.clearTimeout(e.timeout),e.resolve(null))}})},','requestAugmentedBody:(e,t,a,o)=>{if(!r?.active||!i)return Promise.resolve(null);let s=n();return new Promise(n=>{let i=r.setTimeout(()=>{u.delete(s),n(null)},hs);if(u.set(s,{resolve:n,timeout:i}),!m({type:`AUGMENT_REQUEST_BODY`,id:s,requestId:t,route:a,body:e,recoveryMode:o===`compact`?`compact`:null})){let e=u.get(s);e&&(u.delete(s),r?.clearTimeout(e.timeout),e.resolve(null))}})},','main forwarding')
 s=rep(s,'Sa({onRequestBody(t,n,r){return e.requestAugmentedBody(t,n,r)},','Sa({onRequestBody(t,n,r,i){return e.requestAugmentedBody(t,n,r,i)},','main wire')
 wr(p,s)
def transform_content(p):
 s=p.read_text('utf-8-sig')
 s=rep(s,'AUGMENT_REQUEST_BODY:e=>YK(e.id)&&typeof e.body==`string`&&zc(e.route)&&(e.requestId===void 0||YK(e.requestId)),','AUGMENT_REQUEST_BODY:e=>YK(e.id)&&typeof e.body==`string`&&zc(e.route)&&(e.requestId===void 0||YK(e.requestId))&&(e.recoveryMode===void 0||e.recoveryMode===null||e.recoveryMode===`compact`),','content validator')
 s=rep(s,'augmented:typeof t.augmented==`boolean`?t.augmented:null,errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``}','augmented:typeof t.augmented==`boolean`?t.augmented:null,recoveryMode:t.recoveryMode===`compact`?`compact`:null,failureCount:DPP_NUM_331018(t.failureCount),parentMessageId:DPP_NUM_331018(t.parentMessageId),expectedParentMessageId:DPP_NUM_331018(t.expectedParentMessageId),errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``}','preflight metadata')
 needle='descriptorNames:Array.isArray(t.descriptorNames)?t.descriptorNames.filter(e=>typeof e==`string`).slice(0,12).map(e=>e.slice(0,120)):[]';s=rep(s,needle,needle+',recoveryMode:t.recoveryMode===`compact`?`compact`:null','web diag mode')
 s=rep(s,'function Zc(e,t){let n={...e},r=n.prompt,DPPOriginalPrompt331010=r;','''function DPP_COMPACT_SCHEMA_331020(e,t=0){if(!e||typeof e!=`object`||Array.isArray(e)||t>4)return{};let n={};for(let r of[`type`,`enum`,`const`,`required`,`additionalProperties`,`minItems`,`maxItems`,`minimum`,`maximum`])Object.prototype.hasOwnProperty.call(e,r)&&(n[r]=e[r]);if(e.properties&&typeof e.properties==`object`&&!Array.isArray(e.properties)){let r={};for(let[n,i]of Object.entries(e.properties).slice(0,24))r[n]=DPP_COMPACT_SCHEMA_331020(i,t+1);n.properties=r}return e.items&&(n.items=DPP_COMPACT_SCHEMA_331020(e.items,t+1)),Array.isArray(e.anyOf)&&(n.anyOf=e.anyOf.slice(0,6).map(e=>DPP_COMPACT_SCHEMA_331020(e,t+1))),Array.isArray(e.oneOf)&&(n.oneOf=e.oneOf.slice(0,6).map(e=>DPP_COMPACT_SCHEMA_331020(e,t+1))),n}function DPP_COMPACT_DESCRIPTORS_331020(e){return(Array.isArray(e)?e:[]).map(e=>({...e,title:typeof e?.title==`string`?e.title.slice(0,80):e?.name??`tool`,description:typeof e?.description==`string`?e.description.replace(/\\s+/g,` `).slice(0,180):``,inputSchema:DPP_COMPACT_SCHEMA_331020(e?.inputSchema)}))}function Zc(e,t){let n={...e},r=n.prompt,DPPOriginalPrompt331010=r;''','compact helpers')
 s=rep(s,'async function bZ(e){let t=typeof e.id==`string`?e.id:``,n=typeof e.requestId==`string`?e.requestId:``;if(!t)return;let r=null,i=``,a=!1;','async function bZ(e){let t=typeof e.id==`string`?e.id:``,n=typeof e.requestId==`string`?e.requestId:``,DPPRecoveryCompact331020=e.recoveryMode===`compact`;if(!t)return;let r=null,i=``,a=!1;','recovery flag')
 s=rep(s,'route:e.route,rawBodyChars:typeof e.body==`string`?e.body.length:null});','route:e.route,rawBodyChars:typeof e.body==`string`?e.body.length:null,recoveryMode:DPPRecoveryCompact331020?`compact`:null});','receive mode')
 s=rep(s,'let u=await kZ(l);DPP_RECORD_PREFLIGHT_331018({stage:`content_project_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i});let d=Zc(l,{chatSessionId:AZ(l),memories:XY,skills:ZY,activePreset:QY,projectContext:u?.context??null,projectId:u?.projectId??null,modelType:$Y,toolDescriptors:r.descriptors,messageCount:oX,locale:nX,promptSettings:eX,skillAutoActivation:tX});','let u=DPPRecoveryCompact331020?null:await kZ(l);DPP_RECORD_PREFLIGHT_331018({stage:`content_project_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i,recoveryMode:DPPRecoveryCompact331020?`compact`:null});let DPPRecoveryDescriptors331020=DPPRecoveryCompact331020?DPP_COMPACT_DESCRIPTORS_331020(r.descriptors):r.descriptors,DPPRecoveryPromptSettings331020=DPPRecoveryCompact331020?{...eX,memoryEnabled:!1,presetCadence:`off`}:eX,d=Zc(l,{chatSessionId:AZ(l),memories:XY,skills:ZY,activePreset:DPPRecoveryCompact331020?null:QY,projectContext:DPPRecoveryCompact331020?null:u?.context??null,projectId:DPPRecoveryCompact331020?null:u?.projectId??null,modelType:$Y,toolDescriptors:DPPRecoveryDescriptors331020,messageCount:oX,locale:nX,promptSettings:DPPRecoveryPromptSettings331020,skillAutoActivation:DPPRecoveryCompact331020?{everyMessage:!1,firstMessage:!1}:tX});','compact augmentation')
 s=rep(s,'authRequestId:i,augmentedBodyChars:d.body.length}),oX=','authRequestId:i,augmentedBodyChars:d.body.length,recoveryMode:DPPRecoveryCompact331020?`compact`:null}),oX=','augment mode')
 s=rep(s,'authRequestId:i,augmentedBodyChars:d.body.length}),FZ({type:`AUGMENT_REQUEST_BODY_RESULT`','authRequestId:i,augmentedBodyChars:d.body.length,recoveryMode:DPPRecoveryCompact331020?`compact`:null}),FZ({type:`AUGMENT_REQUEST_BODY_RESULT`','result mode')
 wr(p,s)
def transform(root):
 transform_content(root/'content-scripts/content.js');transform_main(root/'content-scripts/main-world.js')
 p=root/'manifest.json';m=json.loads(p.read_text('utf-8-sig'))
 if m.get('version')!=OLD_MANIFEST_VERSION or m.get('version_name')!=OLD_VERSION:raise RuntimeError('manifest input version mismatch')
 m['version']=NEW_MANIFEST_VERSION;m['version_name']=NEW_VERSION;wr(p,json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 for rel in ('_locales/en/messages.json','_locales/zh_CN/messages.json'):
  p=root/rel;x=p.read_text('utf-8-sig')
  if 'Fix 3.3.10.19' not in x:raise RuntimeError(f'{rel}: old marker missing')
  wr(p,x.replace('Fix 3.3.10.19','Fix 3.3.10.20'))
def apply(arg):
 root=Path(arg).resolve();paths={r:root/r for r in RELS};m=json.loads(paths['manifest.json'].read_text('utf-8-sig'))
 if m.get('version')==NEW_MANIFEST_VERSION and m.get('version_name')==NEW_VERSION:
  for r,w in OUTPUT_EXPECTED.items():
   g=sha(paths[r]);
   if g!=w:raise RuntimeError(f'already-applied hash mismatch for {r}: {g} != {w}')
  print('APPLY_FIX331020_OK already-applied');return
 if m.get('version')!=OLD_MANIFEST_VERSION or m.get('version_name')!=OLD_VERSION:raise RuntimeError(f'expected {OLD_VERSION}, got {m.get("version_name")!r}')
 for r,w in EXPECTED.items():
  g=sha(paths[r]);
  if g!=w:raise RuntimeError(f'input hash mismatch for {r}: {g} != {w}')
 stage=Path(tempfile.mkdtemp(prefix='.fix331020-stage-',dir=root))
 try:
  for r in RELS:
   d=stage/r;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(paths[r],d)
  transform(stage)
  for r,w in OUTPUT_EXPECTED.items():
   g=sha(stage/r)
   if g!=w:raise RuntimeError(f'staged output hash mismatch for {r}: {g} != {w}')
  for r in RELS:os.replace(stage/r,paths[r])
 finally:shutil.rmtree(stage,ignore_errors=True)
 print('APPLY_FIX331020_OK')
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: apply-fix331020.py <extension-root>')
 apply(sys.argv[1])

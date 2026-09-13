from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
'content':'E69328568FC69010F1F5E729235478E2947CF92E86A7E2200B664D6F2022EE2A',
'manifest':'6AEA403ADB14AA7D4C593AD4A90AA23DE76423A3D2C0E313DEC2FB86EE743B2E',
'en':'087637A990989053E2D807EDB3202C47A37104D7B4FB42DABF7FEBF3BCDC917B',
'zh':'19000524E738D04BC08BAF4A1BC09227DEA751A9DA9E2EC9395501FEA3DD8A1D'}
OLD='1.14.0 ShunCode MCP Fix 3.3.6';NEW='1.14.0 ShunCode MCP Fix 3.3.7';OLDN='DeepSeek++ ShunCode MCP Fix 3.3.6';NEWN='DeepSeek++ ShunCode MCP Fix 3.3.7'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rep(s,a,b,label,count=1):
 c=s.count(a)
 if c!=count:raise RuntimeError(f'{label}: expected {count}, found {c}')
 return s.replace(a,b,count)
def atomic(items):
 tmp=[]
 try:
  for p,s in items:
   q=p.with_name(p.name+'.fix337.tmp');q.write_text(s,encoding='utf8',newline='');tmp.append((q,p))
  for q,p in tmp:os.replace(q,p)
 finally:
  for q,_ in tmp:
   try:q.unlink()
   except FileNotFoundError:pass
def main(root):
 root=Path(root);cp=root/'content-scripts/content.js';mp=root/'manifest.json';ep=root/'_locales/en/messages.json';zp=root/'_locales/zh_CN/messages.json'
 m=json.loads(mp.read_text(encoding='utf-8-sig'));en=json.loads(ep.read_text(encoding='utf-8-sig'));zh=json.loads(zp.read_text(encoding='utf-8-sig'));s=cp.read_text(encoding='utf-8-sig')
 if m.get('version_name')==NEW and m.get('version')=='1.14.0.2' and 'DPP_AGENT_SYNTHETIC_REF_FILES_337' in s and 'DPP_JSON_COMPLETION_ERROR_337' in s:
  print('APPLY_FIX337_ALREADY_APPLIED');return 0
 if m.get('version_name')!=OLD or m.get('version')!='1.14.0.1':raise RuntimeError('expected Fix 3.3.6 baseline')
 for k,p in [('content',cp),('manifest',mp),('en',ep),('zh',zp)]:
  got=h(p)
  if got!=EXPECTED[k]:raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 # Synthetic Agent turns follow an already-created assistant message. Do not re-attach the original user files on every continuation.
 old='promptOptions:{modelType:e.promptOptions.modelType,searchEnabled:e.promptOptions.searchEnabled,thinkingEnabled:e.promptOptions.thinkingEnabled,refFileIds:e.promptOptions.refFileIds},toolDescriptors:'
 new='promptOptions:{modelType:e.promptOptions.modelType,searchEnabled:e.promptOptions.searchEnabled,thinkingEnabled:e.promptOptions.thinkingEnabled,refFileIds:DPP_AGENT_SYNTHETIC_REF_FILES_337},toolDescriptors:'
 s=rep(s,old,new,'agent synthetic ref files')
 anchor='async function J$(e,t){if(X$(e))return;'
 s=rep(s,anchor,'var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];'+anchor,'agent ref marker')
 # HTTP 200 JSON is a business/application response, not SSE. Surface only safe code/message fields; never raw body.
 old='async function WL(e,t,n){let r=await GL(e,{signal:n});if(!r.ok)throw new AL(await tR(r),{retryable:!0});if(!r.body)throw new AL(`DeepSeek completion response did not include a stream body.`,{retryable:!0});let i=await qL(r,t.onTokenSpeed?{...t,onTokenSpeed(n){t.onTokenSpeed?.({...n,chatSessionId:e.chatSessionId,modelType:n.modelType??e.modelType})}}:t);return i.dppHttpStatus=r.status,i.dppContentType=String(r.headers.get(`content-type`)??``).slice(0,96),i}'
 new='function DPP_JSON_FIELD_337(e,t){for(let n of t){let t=e;for(let e of n.split(`.`)){if(!t||typeof t!=`object`){t=void 0;break}t=t[e]}if(typeof t==`string`&&t.trim())return t.trim();if(typeof t==`number`&&Number.isFinite(t))return String(t)}return null}function DPP_JSON_COMPLETION_ERROR_337(e,t){let n=null;try{let e=JSON.parse(t);if(e&&typeof e==`object`&&!Array.isArray(e))n=e}catch{}let r=n?DPP_JSON_FIELD_337(n,[`biz_code`,`code`,`error.code`,`data.biz_code`,`data.code`]):null,i=n?DPP_JSON_FIELD_337(n,[`biz_msg`,`msg`,`message`,`error.message`,`data.biz_msg`,`data.msg`,`data.message`]):null,a=i?i.replace(/\\s+/g,` `).slice(0,240):null,o=[`DeepSeek completion returned JSON instead of an SSE stream (HTTP ${e.status}).`];return r&&o.push(`code=${r}`),a&&o.push(`message=${a}`),o.join(` `)}async function WL(e,t,n){let r=await GL(e,{signal:n});if(!r.ok)throw new AL(await tR(r),{retryable:!0});if(!r.body)throw new AL(`DeepSeek completion response did not include a stream body.`,{retryable:!0});let a=String(r.headers.get(`content-type`)??``).slice(0,96);if(/(?:application|text)\\/(?:[A-Za-z0-9.+-]*\\+)?json(?:\\s*;|$)/i.test(a)){let e=await nL(r,`DeepSeek completion`),t=new AL(DPP_JSON_COMPLETION_ERROR_337(r,e),{retryable:!1});throw t.dppNoRetry337=!0,t}let i=await qL(r,t.onTokenSpeed?{...t,onTokenSpeed(n){t.onTokenSpeed?.({...n,chatSessionId:e.chatSessionId,modelType:n.modelType??e.modelType})}}:t);return i.dppHttpStatus=r.status,i.dppContentType=a,i}'
 s=rep(s,old,new,'json completion handling')
 # JSON/business responses are explicit non-SSE application responses; do not replay them with fresh PoW.
 old='}catch(e){if(i.aborted)throw e;let t=o.timedOut();if(t&&a)throw Error(`DeepSeek agent step timed out while streaming; the response was interrupted.`);if(a)throw e;if(n>=zR)throw t?Error(`DeepSeek agent step timed out after retry.`):e;if(await LR(i),i.aborted)throw e}finally{o.clear()}}'
 new='}catch(e){if(i.aborted)throw e;if(e?.dppNoRetry337===!0)throw e;let t=o.timedOut();if(t&&a)throw Error(`DeepSeek agent step timed out while streaming; the response was interrupted.`);if(a)throw e;if(n>=zR)throw t?Error(`DeepSeek agent step timed out after retry.`):e;if(await LR(i),i.aborted)throw e}finally{o.clear()}}'
 s=rep(s,old,new,'json response no replay')
 m['version']='1.14.0.2';m['version_name']=NEW
 for obj in (en,zh):
  for key in ('extension_name','extension_action_title'):
   if key in obj and isinstance(obj[key],dict) and obj[key].get('message')==OLDN:obj[key]['message']=NEWN
   elif key in obj and isinstance(obj[key],dict):raise RuntimeError(f'{key} locale old name mismatch')
 atomic([(cp,s),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]);print('APPLY_FIX337_PASS');return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]))
 except Exception as e:print('APPLY_FIX337_FAIL:',e,file=sys.stderr);sys.exit(1)
from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
'content':'E4F9727B092640C93C746F80296541D3155DC9BA4A30C44D429F35182BF0596F',
'background':'6039A7EF6CF81133FB6C836B18B8024E379D764D4934DC2F142A994FDB3EF16D',
'manifest':'0D7D322ED81D7A9758F2DFE43AD202CCC68E7BC7CE0167C82690F2A1E7711D96',
'en':'6D7F57A37177910F4A8A08EEC2A7A59112970F366B20A51E7FCCA9FA1DCF6249',
'zh':'68E75BD6F05E98C35A1E6B04F4D411D54634BA851B28DF0881693B9FD7DE8536'}
OLD='1.14.0 ShunCode MCP Fix 3.3.4'; NEW='1.14.0 ShunCode MCP Fix 3.3.5'
OLDN='DeepSeek++ ShunCode MCP Fix 3.3.4'; NEWN='DeepSeek++ ShunCode MCP Fix 3.3.5'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rep(s,a,b,label,count=1):
 c=s.count(a)
 if c!=count: raise RuntimeError(f'{label}: expected {count}, found {c}')
 return s.replace(a,b,count)
def atomic(items):
 tmp=[]
 try:
  for p,s in items:
   q=p.with_name(p.name+'.fix335.tmp'); q.write_text(s,encoding='utf-8',newline=''); tmp.append((q,p))
  for q,p in tmp: os.replace(q,p)
 finally:
  for q,_ in tmp:
   try:q.unlink()
   except FileNotFoundError:pass
def main(root):
 root=Path(root); cp=root/'content-scripts/content.js'; bp=root/'background.js'; mp=root/'manifest.json'; ep=root/'_locales/en/messages.json'; zp=root/'_locales/zh_CN/messages.json'
 m=json.loads(mp.read_text(encoding='utf-8-sig')); en=json.loads(ep.read_text(encoding='utf-8-sig')); zh=json.loads(zp.read_text(encoding='utf-8-sig'))
 s=cp.read_text(encoding='utf-8-sig')
 if m.get('version_name')==NEW and 'DPP_FRESH_POW_RETRY_335' in s:
  print('APPLY_FIX335_ALREADY_APPLIED'); return 0
 if m.get('version_name')!=OLD: raise RuntimeError('expected Fix 3.3.4 manifest')
 for k,p in [('content',cp),('background',bp),('manifest',mp),('en',ep),('zh',zp)]:
  got=h(p)
  if got!=EXPECTED[k]: raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 # response state diagnostics
 a='function hI(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,dppStreamEvents:[]}}'
 b='function hI(){return{assistantText:``,assistantReasoningText:``,responseMessageId:null,requestMessageId:null,finished:!1,dppStreamEvents:[],dppStreamBytes:0,dppStreamChunks:0,dppHttpStatus:null,dppContentType:``,dppAttempt:1,dppFreshPow:!1}}'
 s=rep(s,a,b,'stream state diagnostics')
 # response status/content-type diagnostics
 a='async function WL(e,t,n){let r=await GL(e,{signal:n});if(!r.ok)throw new AL(await tR(r),{retryable:!0});if(!r.body)throw new AL(`DeepSeek completion response did not include a stream body.`,{retryable:!0});return qL(r,t.onTokenSpeed?{...t,onTokenSpeed(n){t.onTokenSpeed?.({...n,chatSessionId:e.chatSessionId,modelType:n.modelType??e.modelType})}}:t)}'
 b='async function WL(e,t,n){let r=await GL(e,{signal:n});if(!r.ok)throw new AL(await tR(r),{retryable:!0});if(!r.body)throw new AL(`DeepSeek completion response did not include a stream body.`,{retryable:!0});let i=await qL(r,t.onTokenSpeed?{...t,onTokenSpeed(n){t.onTokenSpeed?.({...n,chatSessionId:e.chatSessionId,modelType:n.modelType??e.modelType})}}:t);return i.dppHttpStatus=r.status,i.dppContentType=String(r.headers.get(`content-type`)??``).slice(0,96),i}'
 s=rep(s,a,b,'http stream diagnostics')
 # raw byte/chunk count in stream reader
 a='async function qL(e,t){let n=e.body.getReader(),r=gI(),i=hI(),a=t.retainAssistantText!==!1,o=t.onTokenSpeed?wl(e=>t.onTokenSpeed?.({...e,assistantMessageId:i.responseMessageId}),FL):null,s=o?(e,t)=>{o.updateServerStats(TI(e,t.type));let n=jI(e);n&&o.append(n),UI(e)&&o.finish()}:void 0;t'
 b='async function qL(e,t){let n=e.body.getReader(),r=gI(),i=hI(),a=t.retainAssistantText!==!1,o=t.onTokenSpeed?wl(e=>t.onTokenSpeed?.({...e,assistantMessageId:i.responseMessageId}),FL):null,s=o?(e,t)=>{o.updateServerStats(TI(e,t.type));let n=jI(e);n&&o.append(n),UI(e)&&o.finish()}:void 0;t'
 # replace only the read loop fragment to avoid huge exact function body
 frag='let{done:e,value:o}=await n.read();if(e)break;let c=yI(r.push(o),i,{retainAssistantText:a,onParsed:s,onReasoningChunk:t.onReasoningChunk});'
 frag2='let{done:e,value:o}=await n.read();if(e)break;i.dppStreamChunks+=1,i.dppStreamBytes+=o?.byteLength??0;let c=yI(r.push(o),i,{retainAssistantText:a,onParsed:s,onReasoningChunk:t.onReasoningChunk});'
 s=rep(s,frag,frag2,'raw stream byte diagnostics')
 # fresh PoW/auth for retry attempts. First request behavior is preserved; only retries rebuild credentials/challenge.
 a='function BR(e={}){let{powWasmUrl:t}=e;return async(e,n,r)=>{let i=BL(),a=await LL(i,t);return HR({chatSessionId:e.chatSessionId,parentMessageId:e.parentMessageId,modelType:e.modelType,prompt:e.prompt,refFileIds:e.refFileIds,thinkingEnabled:e.thinkingEnabled,searchEnabled:e.searchEnabled,clientHeaders:i,powHeaders:a},n,r)}}'
 b='var DPP_FRESH_POW_RETRY_335=!0;function BR(e={}){let{powWasmUrl:t}=e;return async(e,n,r)=>{let i=async()=>{let i=BL(),a=await LL(i,t);return{chatSessionId:e.chatSessionId,parentMessageId:e.parentMessageId,modelType:e.modelType,prompt:e.prompt,refFileIds:e.refFileIds,thinkingEnabled:e.thinkingEnabled,searchEnabled:e.searchEnabled,clientHeaders:i,powHeaders:a}};return HR(await i(),n,r,i)}}'
 s=rep(s,a,b,'fresh pow request factory')
 a='async function HR(e,t,n){let r=n??new AbortController().signal,i=!1;for(let n=1;n<=zR;n++){let a=IR(r);try{let o=await WL(e,{retainAssistantText:!1,onTextChunk(e,n){i=!0,t.onTextChunk(e,n)},onReasoningChunk(e,n){i=!0,t.onReasoningChunk?.(e,n)},onTokenSpeed:t.onTokenSpeed},a.signal),s=!o.finished&&!i&&o.responseMessageId==null&&o.requestMessageId==null&&n<zR;if(s){if(await LR(r),r.aborted)throw new DOMException(`DeepSeek request was aborted.`,`AbortError`);continue}return{assistantText:o.assistantText,responseMessageId:o.responseMessageId,requestMessageId:o.requestMessageId,finished:o.finished,streamEvents:Array.isArray(o.dppStreamEvents)?o.dppStreamEvents:[]}}catch(e){if(r.aborted)throw e;let t=a.timedOut();if(t&&i)throw Error(`DeepSeek agent step timed out while streaming; the response was interrupted.`);if(n>=zR)throw t?Error(`DeepSeek agent step timed out after retry.`):e;if(await LR(r),r.aborted)throw e}finally{a.clear()}}throw Error(`DeepSeek agent step failed without a completed attempt.`)}'
 b='async function HR(e,t,n,r){let i=n??new AbortController().signal,a=!1;for(let n=1;n<=zR;n++){let o=IR(i);try{n>1&&typeof r==`function`&&(e=await r());let s=await WL(e,{retainAssistantText:!1,onTextChunk(e,n){a=!0,t.onTextChunk(e,n)},onReasoningChunk(e,n){a=!0,t.onReasoningChunk?.(e,n)},onTokenSpeed:t.onTokenSpeed},o.signal);s.dppAttempt=n,s.dppFreshPow=n>1&&typeof r==`function`;let c=!s.finished&&!a&&s.responseMessageId==null&&s.requestMessageId==null&&n<zR;if(c){if(await LR(i),i.aborted)throw new DOMException(`DeepSeek request was aborted.`,`AbortError`);continue}return{assistantText:s.assistantText,responseMessageId:s.responseMessageId,requestMessageId:s.requestMessageId,finished:s.finished,streamEvents:Array.isArray(s.dppStreamEvents)?s.dppStreamEvents:[],streamDiagnostics:{attempt:n,httpStatus:s.dppHttpStatus,contentType:s.dppContentType,bytes:s.dppStreamBytes,chunks:s.dppStreamChunks,freshPow:s.dppFreshPow}}}catch(e){if(i.aborted)throw e;let t=o.timedOut();if(t&&a)throw Error(`DeepSeek agent step timed out while streaming; the response was interrupted.`);if(a)throw e;if(n>=zR)throw t?Error(`DeepSeek agent step timed out after retry.`):e;if(await LR(i),i.aborted)throw e}finally{o.clear()}}throw Error(`DeepSeek agent step failed without a completed attempt.`)}'
 s=rep(s,a,b,'fresh pow retry loop')
 # surface privacy-safe diagnostics when no stream markers exist or when useful
 a='if(!ie.finished&&!d?.aborted){let e=Array.isArray(ie.streamEvents)&&ie.streamEvents.length?` Last stream markers: ${JSON.stringify(ie.streamEvents).slice(0,1200)}`:``;throw Error(`DeepSeek response stream ended before completion (the response was interrupted).${e}`)}'
 b='if(!ie.finished&&!d?.aborted){let e=Array.isArray(ie.streamEvents)&&ie.streamEvents.length?` Last stream markers: ${JSON.stringify(ie.streamEvents).slice(0,1200)}`:``,t=ie.streamDiagnostics&&typeof ie.streamDiagnostics==`object`?` Stream diagnostics: ${JSON.stringify(ie.streamDiagnostics).slice(0,500)}`:``;throw Error(`DeepSeek response stream ended before completion (the response was interrupted).${e}${t}`)}'
 s=rep(s,a,b,'stream diagnostic error')
 # metadata
 m['version_name']=NEW
 for obj in (en,zh):
  for key in ('extension_name','extension_action_title'):
   if key in obj and isinstance(obj[key],dict) and obj[key].get('message')==OLDN: obj[key]['message']=NEWN
   elif key in obj and isinstance(obj[key],dict): raise RuntimeError(f'{key} locale does not match expected old name')
 items=[(cp,s),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]
 atomic(items);print('APPLY_FIX335_PASS');return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]))
 except Exception as e:print('APPLY_FIX335_FAIL:',e,file=sys.stderr);sys.exit(1)
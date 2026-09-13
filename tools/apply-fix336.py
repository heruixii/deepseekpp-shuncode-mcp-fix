from pathlib import Path
import hashlib,json,os,sys
EXPECTED={
'content':'34B05E74371A27EC0BF1EAE9E8414799A81C5522D969E2A78CA3550658E3AC04',
'background':'6039A7EF6CF81133FB6C836B18B8024E379D764D4934DC2F142A994FDB3EF16D',
'manifest':'D0354A50FF5EAC713A286BB342DE38D623F08224933E32BF6F596FF8A90D604C',
'en':'51C2DA7ABDB690DEC8559A2797BF5CF3D3BF792EB5D28AFDC839C1CF60002105',
'zh':'15CDB4A472444093B9308199899340CB78B9E4FCA424A3702AF63120D13C932E'}
OLD='1.14.0 ShunCode MCP Fix 3.3.5';NEW='1.14.0 ShunCode MCP Fix 3.3.6'
OLDN='DeepSeek++ ShunCode MCP Fix 3.3.5';NEWN='DeepSeek++ ShunCode MCP Fix 3.3.6'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rep(s,a,b,label,count=1):
 c=s.count(a)
 if c!=count:raise RuntimeError(f'{label}: expected {count}, found {c}')
 return s.replace(a,b,count)
def atomic(items):
 tmp=[]
 try:
  for p,s in items:
   q=p.with_name(p.name+'.fix336.tmp');q.write_text(s,encoding='utf-8',newline='');tmp.append((q,p))
  for q,p in tmp:os.replace(q,p)
 finally:
  for q,_ in tmp:
   try:q.unlink()
   except FileNotFoundError:pass
def main(root):
 root=Path(root);cp=root/'content-scripts/content.js';bp=root/'background.js';mp=root/'manifest.json';ep=root/'_locales/en/messages.json';zp=root/'_locales/zh_CN/messages.json'
 m=json.loads(mp.read_text(encoding='utf-8-sig'));en=json.loads(ep.read_text(encoding='utf-8-sig'));zh=json.loads(zp.read_text(encoding='utf-8-sig'))
 s=cp.read_text(encoding='utf-8-sig');bg=bp.read_text(encoding='utf-8-sig')
 if m.get('version_name')==NEW and m.get('version')=='1.14.0.1' and 'DPP_EXEC_BLOCK_BUDGET_336' in s and 'DPP_TRIM_TOOL_HISTORY_ON_START_336' in bg:
  print('APPLY_FIX336_ALREADY_APPLIED');return 0
 if m.get('version_name')!=OLD or m.get('version')!='1.14.0':raise RuntimeError('expected Fix 3.3.5 manifest/version')
 for k,p in [('content',cp),('background',bp),('manifest',mp),('en',ep),('zh',zp)]:
  got=h(p)
  if got!=EXPECTED[k]:raise RuntimeError(f'{k} hash mismatch {got} != {EXPECTED[k]}')
 # Tool execution block storage: compact each block and cap whole array. This also migrates legacy oversized records on read.
 old='var lU=Object.freeze({decode:cU,encode(e){return cU(e)}}),uU=`dpp_tool_execution_blocks`,dU=1e3*60*60*24*30;function fU(e=Zo(uU)){let t=Qo({label:`toolExecutionBlocks`,createDefault:()=>[],codec:lU,storage:e});return{read:()=>t.read(),async upsert(e,n=Date.now()){await wi(async()=>{let r=lU.decode([e],`toolExecutionBlocks.upsert`)[0],i=[...(await t.readAlreadyLocked()).filter(e=>e.id!==r.id),r].filter(e=>n-e.createdAt<dU).slice(-100);await t.writeAfterReadAlreadyLocked(i)})}}}'
 new='var lU=Object.freeze({decode:cU,encode(e){return cU(e)}}),uU=`dpp_tool_execution_blocks`,dU=1e3*60*60*24*30,DPP_EXEC_BLOCK_BUDGET_336=262144,DPP_EXEC_BLOCK_SINGLE_BUDGET_336=65536,DPP_EXEC_BLOCK_MAX_EXECUTIONS_336=64;function DPP_EXEC_BLOCK_BYTES_336(e){try{return new TextEncoder().encode(JSON.stringify(e)).length}catch{return Number.POSITIVE_INFINITY}}function DPP_COMPACT_EXEC_BLOCK_336(e,t=DPP_EXEC_BLOCK_SINGLE_BUDGET_336,n=DPP_EXEC_BLOCK_MAX_EXECUTIONS_336){let r={...e,executions:[...(e.executions??[])].slice(-n),metadata:{...e.metadata??{}}};for(;r.executions.length>1&&DPP_EXEC_BLOCK_BYTES_336(r)>t;)r={...r,executions:r.executions.slice(1)};return r.metadata={...r.metadata,toolCount:r.executions.length,mcpToolCount:r.executions.filter(e=>e.provider?.kind===`mcp`).length},r}function DPP_TRIM_EXEC_BLOCKS_336(e,t=DPP_EXEC_BLOCK_BUDGET_336){let n=e.map(e=>DPP_COMPACT_EXEC_BLOCK_336(e));for(;n.length>1&&DPP_EXEC_BLOCK_BYTES_336(n)>t;)n.shift();return n}function fU(e=Zo(uU)){let t=Qo({label:`toolExecutionBlocks`,createDefault:()=>[],codec:lU,storage:e});return{async read(){return wi(async()=>{let e=await t.readAlreadyLocked(),n=DPP_TRIM_EXEC_BLOCKS_336(e);return(n.length!==e.length||DPP_EXEC_BLOCK_BYTES_336(n)!==DPP_EXEC_BLOCK_BYTES_336(e))&&await t.writeAfterReadAlreadyLocked(n),n})},async upsert(e,n=Date.now()){await wi(async()=>{let r=DPP_COMPACT_EXEC_BLOCK_336(lU.decode([e],`toolExecutionBlocks.upsert`)[0]),i=[...(await t.readAlreadyLocked()).filter(e=>e.id!==r.id),r].filter(e=>n-e.createdAt<dU).slice(-100);i=DPP_TRIM_EXEC_BLOCKS_336(i),await t.writeAfterReadAlreadyLocked(i)})}}}'
 s=rep(s,old,new,'execution block storage')
 # Observer: ignore mutations produced inside our own agent subtree; coalesce official-page changes to one RAF.
 old='function Q$(e,t){let n=()=>{Z$(e);let n=r4(e);if(t.parentElement!==n){n.appendChild(t);return}t.nextSibling&&n.appendChild(t)};n(),RY?.disconnect(),RY=new MutationObserver(n),RY.observe(e,{childList:!0,subtree:!0})}'
 new='function DPP_AGENT_OWN_NODE_336(e){let t=e instanceof Element?e:e?.parentElement;return!!t?.closest?.(`.dpp-agent-container`)}function DPP_AGENT_OBSERVER_IGNORABLE_336(e){return e.length>0&&e.every(e=>{let t=e.target instanceof Element?e.target:e.target?.parentElement;if(t?.closest?.(`.dpp-agent-container`))return!0;let n=[...e.removedNodes];if(n.some(e=>e instanceof Element&&(e.matches(`.dpp-agent-container`)||e.querySelector?.(`.dpp-agent-container`))))return!1;let r=[...e.addedNodes];return r.length>0&&n.length===0&&r.every(DPP_AGENT_OWN_NODE_336)})}function Q$(e,t){let n=()=>{Z$(e);let n=r4(e);if(t.parentElement!==n){n.appendChild(t);return}t.nextSibling&&n.appendChild(t)},r=null,i=null,a=e=>{DPP_AGENT_OBSERVER_IGNORABLE_336(e)||(r===null&&(r=requestAnimationFrame(()=>{r=null,RY===i&&n()})))};n(),RY?.disconnect(),i=new MutationObserver(a),RY=i,RY.observe(e,{childList:!0,subtree:!0})}'
 s=rep(s,old,new,'agent observer filtering')
 # Reasoning streaming: coalesce per animation frame, same as visible text; flush at step/loop completion.
 old='function u1(e){if(e.loopId!==LY||!Q||!e.fullText)return;let t=ZB(Q),n=IY,r=e.fullText;if(n&&n.parentElement===t){let e=aV(n);e&&iV(e,r)}else WY.set(e.stepIndex,r),n&&t&&n.parentElement!==t&&nV(n,t,NX(),r);C0(t=>T0(t,e.stepIndex,{reasoning:r}),{persist:!1})}'
 new='var DPP_REASONING_RAF_336=null,DPP_REASONING_PENDING_336=null;function DPP_APPLY_REASONING_336(e){if(e.loopId!==LY||!Q||!e.fullText)return;let t=ZB(Q),n=IY,r=e.fullText;if(n&&n.parentElement===t){let e=aV(n);e&&iV(e,r)}else WY.set(e.stepIndex,r),n&&t&&n.parentElement!==t&&nV(n,t,NX(),r);C0(t=>T0(t,e.stepIndex,{reasoning:r}),{persist:!1})}function u1(e){e.loopId!==LY||!Q||!e.fullText||(DPP_REASONING_PENDING_336=e,DPP_REASONING_RAF_336===null&&(DPP_REASONING_RAF_336=requestAnimationFrame(()=>{DPP_REASONING_RAF_336=null;let e=DPP_REASONING_PENDING_336;DPP_REASONING_PENDING_336=null,e&&DPP_APPLY_REASONING_336(e)})))}function DPP_FLUSH_REASONING_336(){DPP_REASONING_RAF_336!==null&&(cancelAnimationFrame(DPP_REASONING_RAF_336),DPP_REASONING_RAF_336=null);let e=DPP_REASONING_PENDING_336;DPP_REASONING_PENDING_336=null,e&&DPP_APPLY_REASONING_336(e)}'
 s=rep(s,old,new,'reasoning throttle')
 old='function p1(){HY!==null&&(cancelAnimationFrame(HY),HY=null);let e=UY;UY=null,e&&d1(e)}function m1(){HY!==null&&(cancelAnimationFrame(HY),HY=null),UY=null}'
 new='function p1(){HY!==null&&(cancelAnimationFrame(HY),HY=null);let e=UY;UY=null,e&&d1(e),DPP_FLUSH_REASONING_336()}function m1(){HY!==null&&(cancelAnimationFrame(HY),HY=null),UY=null,DPP_REASONING_RAF_336!==null&&(cancelAnimationFrame(DPP_REASONING_RAF_336),DPP_REASONING_RAF_336=null),DPP_REASONING_PENDING_336=null}'
 s=rep(s,old,new,'reasoning flush')
 # Background history migration: existing cap becomes effective immediately after the real extension version update.
 old='function V_(){let e=chrome.storage.local.QUOTA_BYTES??10485760;return Math.min(Math.floor(e*O_),262144)}var H_='
 new='function V_(){let e=chrome.storage.local.QUOTA_BYTES??10485760;return Math.min(Math.floor(e*O_),262144)}async function DPP_TRIM_TOOL_HISTORY_ON_START_336(){let e=F_(C_((await chrome.storage.local.get(E_))[E_])),t=V_(),n=B_(e,t).slice(0,D_);(n.length!==e.length||new Blob([JSON.stringify(e)]).size>t)&&await chrome.storage.local.set({[E_]:w_(n)})}var H_='
 bg=rep(bg,old,new,'background history migration helper')
 old='var bR=r(()=>{fR.ensureReady().catch(jR),CR(),DR(),wR(),xR(),yR()'
 new='var bR=r(()=>{fR.ensureReady().catch(jR),DPP_TRIM_TOOL_HISTORY_ON_START_336().catch(e=>Q(`tool_history_trim_336_failed`,e)),CR(),DR(),wR(),xR(),yR()'
 bg=rep(bg,old,new,'background history startup migration')
 # Real MV3 package version bump forces browser update/service-worker replacement.
 m['version']='1.14.0.1';m['version_name']=NEW
 for obj in (en,zh):
  for key in ('extension_name','extension_action_title'):
   if key in obj and isinstance(obj[key],dict) and obj[key].get('message')==OLDN:obj[key]['message']=NEWN
   elif key in obj and isinstance(obj[key],dict):raise RuntimeError(f'{key} locale old name mismatch')
 items=[(cp,s),(bp,bg),(mp,json.dumps(m,ensure_ascii=False,indent=2)+'\n'),(ep,json.dumps(en,ensure_ascii=False,indent=2)+'\n'),(zp,json.dumps(zh,ensure_ascii=False,indent=2)+'\n')]
 atomic(items);print('APPLY_FIX336_PASS');return 0
if __name__=='__main__':
 try:sys.exit(main(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]))
 except Exception as e:print('APPLY_FIX336_FAIL:',e,file=sys.stderr);sys.exit(1)
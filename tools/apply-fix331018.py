from __future__ import annotations
import hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
EXPECTED={'content-scripts/content.js': '592F3B0A797A4B26AF613B63CD3787555FAD90B1F6D04588C49FBDFC7C9EA4C4', 'content-scripts/main-world.js': '75B63C0A0921C7C7CB955E8A518DCDE2C2E59CF4923F11CDE1D1505C71A6C639', 'manifest.json': '76672787E161EA974397547E3A54E985F64B8EB11EBB532158DF31A2485865DC', '_locales/en/messages.json': '5EFC76BB6FAB208B2E3D3201BCCBF112D731592DD63FB36ABDBE20DE50A3FA55', '_locales/zh_CN/messages.json': 'C9C4BE0ED306EF099B3BE4095C530E3B10D2838E89284CC882E6C3FA6BEBFCF3'}
OUTPUT_EXPECTED={'content-scripts/content.js': 'DFAE734C0A6D277FCA11CB671E5D28AADE69E77D1A155CED19B5AA3E4AFAF410', 'content-scripts/main-world.js': 'D2C47A42FE0229A406ECD674C9409F893ABD3B95D2B7D691B103059529BA0C2F', 'manifest.json': '467092B1F878C8F4A7B690960C1D5A509B59827FE5997721D6B885FD85ED1E34', '_locales/en/messages.json': '6A9091365FB35EEC12D21CB18ACB3B53DFAC864897BF46ACDA5B1AA1F577F277', '_locales/zh_CN/messages.json': '9812C39828D51FCC5362BF7A87336AF10B48D807BAD29CFD4CBF62F477906AC0'}
OLD_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.17'
NEW_VERSION='1.14.0 ShunCode MCP Fix 3.3.10.18'
OLD_MANIFEST_VERSION='1.14.0.22'
NEW_MANIFEST_VERSION='1.14.0.23'
RELS=['content-scripts/content.js', 'content-scripts/main-world.js', 'manifest.json', '_locales/en/messages.json', '_locales/zh_CN/messages.json']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def rep(s,old,new,label,count=1):
    c=s.count(old)
    if c!=count: raise RuntimeError(f'{label}: expected {count} marker(s), found {c}')
    return s.replace(old,new,count)
def transform(dst):
    p=dst/'content-scripts/main-world.js';s=p.read_text('utf-8-sig')
    s=rep(s,'`RESPONSE_COMPLETE`,`REQUEST_TERMINAL`,`RESPONSE_TOKEN_SPEED`','`RESPONSE_COMPLETE`,`REQUEST_TERMINAL`,`REQUEST_PREFLIGHT_DIAG`,`RESPONSE_TOKEN_SPEED`','mw types')
    s=rep(s,'RESPONSE_COMPLETE:X.mainWorld,REQUEST_TERMINAL:X.mainWorld,RESPONSE_TOKEN_SPEED:X.mainWorld','RESPONSE_COMPLETE:X.mainWorld,REQUEST_TERMINAL:X.mainWorld,REQUEST_PREFLIGHT_DIAG:X.mainWorld,RESPONSE_TOKEN_SPEED:X.mainWorld','mw source')
    s=rep(s,'RESPONSE_COMPLETE:e=>Qo(e.payload),REQUEST_TERMINAL:e=>$(e.payload)&&Q(e.payload.requestId),RESPONSE_TOKEN_SPEED:e=>es(e.payload)','RESPONSE_COMPLETE:e=>Qo(e.payload),REQUEST_TERMINAL:e=>$(e.payload)&&Q(e.payload.requestId),REQUEST_PREFLIGHT_DIAG:e=>$(e.data)&&Q(e.data.stage)&&(e.data.requestId===void 0||Q(e.data.requestId)),RESPONSE_TOKEN_SPEED:e=>es(e.payload)','mw validator')
    s=rep(s,'onResponseComplete:()=>{},onRequestTerminal:()=>{},onMemoriesUsed:()=>{}','onResponseComplete:()=>{},onRequestTerminal:()=>{},onRequestPreflight:()=>{},onMemoriesUsed:()=>{}','mw U callback')
    # helper after U assignment
    s=rep(s,'var U=xa();function Sa(e){','var U=xa();function DPP_PREFLIGHT_331018(e){try{U.onRequestPreflight(e)}catch{}}function Sa(e){','mw helper')
    # fetch instrumentation
    old='let c=ja(n.body),l=[...U.toolDescriptors],u=null,d=!1;try{u=await U.onRequestBody(n.body,c.requestId,a)}catch(e){d=!0,console.error(`[DeepSeek++] fetch request augmentation failed; sending original request`,e)}'
    new='let c=ja(n.body),l=[...U.toolDescriptors],u=null,d=!1,DPPAugmentStart331018=performance.now();DPP_PREFLIGHT_331018({stage:`mw_intercept_seen`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId}),DPP_PREFLIGHT_331018({stage:`mw_augment_begin`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId});try{u=await U.onRequestBody(n.body,c.requestId,a),DPP_PREFLIGHT_331018({stage:`mw_augment_result`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId,augmented:u!==null,augmentMs:Math.round(performance.now()-DPPAugmentStart331018)})}catch(e){d=!0,DPP_PREFLIGHT_331018({stage:`mw_augment_error`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:c.chatSessionId,errorName:e instanceof Error?e.name:`Error`,augmentMs:Math.round(performance.now()-DPPAugmentStart331018)}),console.error(`[DeepSeek++] fetch request augmentation failed; sending original request`,e)}'
    s=rep(s,old,new,'fetch augment')
    old='p=u?{...n,body:u.body}:n;return to(e.call(this,t,p),{...f,dppRequestDiag331015:'
    new='p=u?{...n,body:u.body}:n;return DPP_PREFLIGHT_331018({stage:`mw_transport_started`,requestId:c.requestId,route:a,rawBodyChars:n.body.length,augmentedBodyChars:(u?.body??n.body).length,chatSessionId:f.chatSessionId??null}),to(e.call(this,t,p),{...f,dppRequestDiag331015:'
    s=rep(s,old,new,'fetch transport')
    # XHR instrumentation
    old='let t=this,i=async()=>{let i=ja(e),o=null;try{U.onHeadersCaptured(Ea(n.get(t)));let s=[...U.toolDescriptors],c=null,l=!1;try{c=await U.onRequestBody(e,i.requestId,r)}catch(e){l=!0,console.error(`[DeepSeek++] XHR request augmentation failed; sending original request`,e)}'
    new='let t=this,i=async()=>{let i=ja(e),o=null,DPPAugmentStart331018=performance.now();DPP_PREFLIGHT_331018({stage:`mw_intercept_seen`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId}),DPP_PREFLIGHT_331018({stage:`mw_augment_begin`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId});try{U.onHeadersCaptured(Ea(n.get(t)));let s=[...U.toolDescriptors],c=null,l=!1;try{c=await U.onRequestBody(e,i.requestId,r),DPP_PREFLIGHT_331018({stage:`mw_augment_result`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId,augmented:c!==null,augmentMs:Math.round(performance.now()-DPPAugmentStart331018)})}catch(e){l=!0,DPP_PREFLIGHT_331018({stage:`mw_augment_error`,requestId:i.requestId,route:r,rawBodyChars:e.length,chatSessionId:i.chatSessionId,errorName:e instanceof Error?e.name:`Error`,augmentMs:Math.round(performance.now()-DPPAugmentStart331018)}),console.error(`[DeepSeek++] XHR request augmentation failed; sending original request`,e)}'
    s=rep(s,old,new,'xhr augment')
    old='o=ro(t,v),a.call(t,u)}catch(e)'
    new='o=ro(t,v),DPP_PREFLIGHT_331018({stage:`mw_transport_started`,requestId:i.requestId,route:r,rawBodyChars:e.length,augmentedBodyChars:u.length,chatSessionId:v.chatSessionId??null}),a.call(t,u)}catch(e)'
    s=rep(s,old,new,'xhr transport')
    # wire callback
    old='onRequestTerminal(t){e.post({type:`REQUEST_TERMINAL`,payload:t})},onResponseTokenSpeed(t)'
    new='onRequestTerminal(t){e.post({type:`REQUEST_TERMINAL`,payload:t})},onRequestPreflight(t){e.post({type:`REQUEST_PREFLIGHT_DIAG`,data:t})},onResponseTokenSpeed(t)'
    s=rep(s,old,new,'mw wire')
    p.write_text(s,encoding='utf-8',newline='\r\n')

    # CONTENT
    p=dst/'content-scripts/content.js';s=p.read_text('utf-8-sig')
    s=rep(s,'`RESPONSE_COMPLETE`,`REQUEST_TERMINAL`,`RESPONSE_TOKEN_SPEED`','`RESPONSE_COMPLETE`,`REQUEST_TERMINAL`,`REQUEST_PREFLIGHT_DIAG`,`RESPONSE_TOKEN_SPEED`','content types')
    s=rep(s,'RESPONSE_COMPLETE:wK.mainWorld,REQUEST_TERMINAL:wK.mainWorld,RESPONSE_TOKEN_SPEED:wK.mainWorld','RESPONSE_COMPLETE:wK.mainWorld,REQUEST_TERMINAL:wK.mainWorld,REQUEST_PREFLIGHT_DIAG:wK.mainWorld,RESPONSE_TOKEN_SPEED:wK.mainWorld','content source')
    s=rep(s,'RESPONSE_COMPLETE:e=>LK(e.payload),REQUEST_TERMINAL:e=>XK(e.payload)&&YK(e.payload.requestId),RESPONSE_TOKEN_SPEED:e=>zK(e.payload)','RESPONSE_COMPLETE:e=>LK(e.payload),REQUEST_TERMINAL:e=>XK(e.payload)&&YK(e.payload.requestId),REQUEST_PREFLIGHT_DIAG:e=>XK(e.data)&&YK(e.data.stage)&&(e.data.requestId===void 0||YK(e.data.requestId)),RESPONSE_TOKEN_SPEED:e=>zK(e.payload)','content validator')
    # diagnostics funcs insert
    needle='}async function _Z(e){try{switch(e.type)'
    helper='''}var DPP_PREFLIGHT_DIAG_KEY_331018=`dpp_request_preflight_diag_331018`,DPP_PREFLIGHT_WRITE_CHAIN_331018=Promise.resolve(),DPP_AGENT_TOOL_SHAPE_KEY_331018=`dpp_agent_tool_shape_diag_331018`,DPP_AGENT_TOOL_SHAPE_WRITE_CHAIN_331018=Promise.resolve();function DPP_NUM_331018(e){return typeof e==`number`&&Number.isFinite(e)?e:null}function DPP_RECORD_PREFLIGHT_331018(e){let t=e&&typeof e==`object`&&!Array.isArray(e)?e:{};return DPP_PREFLIGHT_WRITE_CHAIN_331018=DPP_PREFLIGHT_WRITE_CHAIN_331018.then(async()=>{let e=await chrome.storage.local.get(DPP_PREFLIGHT_DIAG_KEY_331018),n=Array.isArray(e?.[DPP_PREFLIGHT_DIAG_KEY_331018])?e[DPP_PREFLIGHT_DIAG_KEY_331018]:[],r={ts:Date.now(),stage:typeof t.stage==`string`?t.stage.slice(0,80):``,requestId:typeof t.requestId==`string`?t.requestId.slice(0,100):``,augmentId:typeof t.augmentId==`string`?t.augmentId.slice(0,100):``,authRequestId:typeof t.authRequestId==`string`?t.authRequestId.slice(0,100):``,route:typeof t.route==`string`?t.route.slice(0,40):``,chatSessionId:typeof t.chatSessionId==`string`?t.chatSessionId.slice(0,100):null,rawBodyChars:DPP_NUM_331018(t.rawBodyChars),augmentedBodyChars:DPP_NUM_331018(t.augmentedBodyChars),augmentMs:DPP_NUM_331018(t.augmentMs),augmented:typeof t.augmented==`boolean`?t.augmented:null,errorName:typeof t.errorName==`string`?t.errorName.slice(0,80):``};n.push(r),n.length>160&&(n=n.slice(-160)),await chrome.storage.local.set({[DPP_PREFLIGHT_DIAG_KEY_331018]:n})}).catch(e=>{console.error(`[DeepSeek++] request preflight diagnostics persistence failed`,e)})}function DPP_RECORD_AGENT_TOOL_SHAPE_331018(e){let t=e&&typeof e==`object`&&!Array.isArray(e)?e:{};return DPP_AGENT_TOOL_SHAPE_WRITE_CHAIN_331018=DPP_AGENT_TOOL_SHAPE_WRITE_CHAIN_331018.then(async()=>{let e=await chrome.storage.local.get(DPP_AGENT_TOOL_SHAPE_KEY_331018),n=Array.isArray(e?.[DPP_AGENT_TOOL_SHAPE_KEY_331018])?e[DPP_AGENT_TOOL_SHAPE_KEY_331018]:[],r={ts:Date.now(),loopId:typeof t.loopId==`string`?t.loopId.slice(0,100):``,chatSessionId:typeof t.chatSessionId==`string`?t.chatSessionId.slice(0,100):null,stepIndex:DPP_NUM_331018(t.stepIndex),callId:typeof t.callId==`string`?t.callId.slice(0,120):``,toolName:typeof t.toolName==`string`?t.toolName.slice(0,120):``,argKind:typeof t.argKind==`string`?t.argKind.slice(0,30):``,argKeys:Array.isArray(t.argKeys)?t.argKeys.filter(e=>typeof e==`string`).slice(0,20).map(e=>e.slice(0,100)):[],requiredKeys:Array.isArray(t.requiredKeys)?t.requiredKeys.filter(e=>typeof e==`string`).slice(0,20).map(e=>e.slice(0,100)):[]};n.push(r),n.length>80&&(n=n.slice(-80)),await chrome.storage.local.set({[DPP_AGENT_TOOL_SHAPE_KEY_331018]:n})}).catch(e=>{console.error(`[DeepSeek++] agent tool-shape diagnostics persistence failed`,e)})}async function _Z(e){try{switch(e.type)'''
    s=rep(s,needle,helper,'diag insert')
    # content switch event
    old='case`REQUEST_TERMINAL`:{let t=e.payload?.requestId;'
    new='case`REQUEST_PREFLIGHT_DIAG`:DPP_RECORD_PREFLIGHT_331018(e.data);break;case`REQUEST_TERMINAL`:{let t=e.payload?.requestId;'
    s=rep(s,old,new,'preflight switch')
    # bZ stages
    old='if(!t)return;let r=null,i=``,a=!1;try{if(typeof e.body!=`string`)'
    new='if(!t)return;let r=null,i=``,a=!1;DPP_RECORD_PREFLIGHT_331018({stage:`content_augment_received`,requestId:n,augmentId:t,route:e.route,rawBodyChars:typeof e.body==`string`?e.body.length:null});try{if(typeof e.body!=`string`)'
    s=rep(s,old,new,'content received')
    old='let o=Kc(e.route,e.body);if(!o){xZ(t);return}DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107();'
    new='let o=Kc(e.route,e.body);if(!o){DPP_RECORD_PREFLIGHT_331018({stage:`content_route_passthrough`,requestId:n,augmentId:t,route:e.route,rawBodyChars:e.body.length}),xZ(t);return}DPP_RECORD_PREFLIGHT_331018({stage:`content_route_parsed`,requestId:n,augmentId:t,route:o.route,rawBodyChars:e.body.length,chatSessionId:typeof o.body?.chat_session_id==`string`?o.body.chat_session_id:null}),DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107();'
    s=rep(s,old,new,'content route')
    old='let c=o.body,l=await QQ(c,{onLongRunning(e){FZ({type:`AUGMENT_REQUEST_BODY_EXTEND_TIMEOUT`,id:t,timeoutMs:e})}});r=await jZ({requestId:i,trigger:`manual_chat`,chatSessionId:AZ(l),toolIntent:l.prompt.slice(0,16e3)}),jJ.set(i,r),MJ.set(n,i);let u=await kZ(l),d=Zc(l,{'
    new='let c=o.body,l=await QQ(c,{onLongRunning(e){FZ({type:`AUGMENT_REQUEST_BODY_EXTEND_TIMEOUT`,id:t,timeoutMs:e})}});DPP_RECORD_PREFLIGHT_331018({stage:`content_after_multimodal`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i}),r=await jZ({requestId:i,trigger:`manual_chat`,chatSessionId:AZ(l),toolIntent:l.prompt.slice(0,16e3)}),DPP_RECORD_PREFLIGHT_331018({stage:`content_auth1_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i}),jJ.set(i,r),MJ.set(n,i);let u=await kZ(l);DPP_RECORD_PREFLIGHT_331018({stage:`content_project_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i});let d=Zc(l,{'
    s=rep(s,old,new,'content stages 1')
    old='skillAutoActivation:tX});oX=d.messageCount,d.usedMemoryIds.length>0&&await O$({type:`TOUCH_MEMORIES`,payload:{ids:d.usedMemoryIds}}),await MZ(i),r=await jZ({requestId:i,trigger:`manual_chat`,chatSessionId:AZ(l),toolIntent:l.prompt.slice(0,16e3),localSkillDir:d.activeLocalSkillDir}),SZ({'
    new='skillAutoActivation:tX});DPP_RECORD_PREFLIGHT_331018({stage:`content_augment_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i,augmentedBodyChars:d.body.length}),oX=d.messageCount,d.usedMemoryIds.length>0&&await O$({type:`TOUCH_MEMORIES`,payload:{ids:d.usedMemoryIds}}),await MZ(i),DPP_RECORD_PREFLIGHT_331018({stage:`content_auth_close_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i}),r=await jZ({requestId:i,trigger:`manual_chat`,chatSessionId:AZ(l),toolIntent:l.prompt.slice(0,16e3),localSkillDir:d.activeLocalSkillDir}),DPP_RECORD_PREFLIGHT_331018({stage:`content_auth2_done`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i}),SZ({'
    s=rep(s,old,new,'content stages 2')
    old='if(a=!1,f)throw Error(`Request ended before its tool authorization became active.`);FZ({type:`AUGMENT_REQUEST_BODY_RESULT`,id:t,ok:!0,result:{body:d.body'
    new='if(a=!1,f)throw Error(`Request ended before its tool authorization became active.`);DPP_RECORD_PREFLIGHT_331018({stage:`content_result_posted`,requestId:n,augmentId:t,route:o.route,chatSessionId:AZ(l),authRequestId:i,augmentedBodyChars:d.body.length}),FZ({type:`AUGMENT_REQUEST_BODY_RESULT`,id:t,ok:!0,result:{body:d.body'
    s=rep(s,old,new,'content result')
    old='}catch(e){if(r&&await MZ(i),BZ(e)){VZ(),xZ(t);return}FZ({type:`AUGMENT_REQUEST_BODY_RESULT`,id:t,ok:!1,error:e instanceof Error?e.message:String(e)})}finally{'
    new='}catch(e){DPP_RECORD_PREFLIGHT_331018({stage:`content_augment_error`,requestId:n,augmentId:t,route:typeof e?.route==`string`?e.route:``,authRequestId:i,errorName:e instanceof Error?e.name:`Error`});if(r&&await MZ(i),BZ(e)){VZ(),xZ(t);return}FZ({type:`AUGMENT_REQUEST_BODY_RESULT`,id:t,ok:!1,error:e instanceof Error?e.message:String(e)})}finally{'
    s=rep(s,old,new,'content error')
    # Agent tool shape at execution start
    old='case`tool_execution_start`:he(e.toolCallId,e.toolName,e.args);break;case`tool_execution_end`:'
    new='case`tool_execution_start`:{let t=v.get(e.toolName),r=e.args,k=r&&typeof r==`object`&&!Array.isArray(r)?Object.keys(r):[];DPP_RECORD_AGENT_TOOL_SHAPE_331018({loopId:a,chatSessionId:s,stepIndex:b,callId:e.toolCallId,toolName:e.toolName,argKind:Array.isArray(r)?`array`:r===null?`null`:typeof r,argKeys:k,requiredKeys:Array.isArray(t?.parameters?.required)?t.parameters.required:[]}),he(e.toolCallId,e.toolName,e.args);break}case`tool_execution_end`:'
    s=rep(s,old,new,'agent shape')
    p.write_text(s,encoding='utf-8',newline='\r\n')
    # earliest send-hook breadcrumb, before extension readiness wait
    p=dst/'content-scripts/main-world.js';s=p.read_text('utf-8-sig')
    old='if(Na(n.headers))return e.call(this,t,{...n,headers:Pa(n.headers)});await Aa(),U.onHeadersCaptured(Ea(n.headers));let c=ja(n.body),l=[...U.toolDescriptors]'
    new='if(Na(n.headers))return e.call(this,t,{...n,headers:Pa(n.headers)});let DPPInitialRequest331018=ja(n.body);DPP_PREFLIGHT_331018({stage:`mw_send_hook_seen`,requestId:DPPInitialRequest331018.requestId,route:a,rawBodyChars:n.body.length,chatSessionId:DPPInitialRequest331018.chatSessionId});await Aa(),U.onHeadersCaptured(Ea(n.headers));let c=DPPInitialRequest331018,l=[...U.toolDescriptors]'
    s=rep(s,old,new,'fetch earliest send hook')
    old='if(s(r)&&typeof e==`string`){let t=this,i=async()=>{let i=ja(e),o=null,DPPAugmentStart331018=performance.now();'
    new='if(s(r)&&typeof e==`string`){let t=this,DPPInitialRequest331018=ja(e);DPP_PREFLIGHT_331018({stage:`mw_send_hook_seen`,requestId:DPPInitialRequest331018.requestId,route:r,rawBodyChars:e.length,chatSessionId:DPPInitialRequest331018.chatSessionId});let i=async()=>{let i=DPPInitialRequest331018,o=null,DPPAugmentStart331018=performance.now();'
    s=rep(s,old,new,'xhr earliest send hook')
    p.write_text(s,encoding='utf-8',newline='\r\n')
    p=dst/'manifest.json';m=json.loads(p.read_text('utf-8-sig'));assert m['version']=='1.14.0.22';m['version']='1.14.0.23';m['version_name']='1.14.0 ShunCode MCP Fix 3.3.10.18';p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
     p=dst/rel;x=p.read_text('utf-8-sig');assert 'Fix 3.3.10.17' in x;p.write_text(x.replace('Fix 3.3.10.17','Fix 3.3.10.18'),encoding='utf-8',newline='\r\n')

def apply(arg):
    root=Path(arg).resolve()
    paths={r:root/r for r in RELS}
    manifest=json.loads(paths['manifest.json'].read_text(encoding='utf-8-sig'))
    if manifest.get('version')==NEW_MANIFEST_VERSION and manifest.get('version_name')==NEW_VERSION:
        for r,w in OUTPUT_EXPECTED.items():
            got=sha(paths[r])
            if got!=w: raise RuntimeError(f'already-applied hash mismatch for {r}: {got}')
        print('APPLY_FIX331018_OK already-applied'); return
    if manifest.get('version')!=OLD_MANIFEST_VERSION or manifest.get('version_name')!=OLD_VERSION:
        raise RuntimeError(f'expected {OLD_VERSION}, got {manifest.get("version_name")!r}')
    for r,w in EXPECTED.items():
        got=sha(paths[r])
        if got!=w: raise RuntimeError(f'input hash mismatch for {r}: {got}')
    stage=Path(tempfile.mkdtemp(prefix='.fix331018-stage-',dir=root))
    try:
        for r in RELS:
            d=stage/r; d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(paths[r],d)
        transform(stage)
        for r,w in OUTPUT_EXPECTED.items():
            got=sha(stage/r)
            if got!=w: raise RuntimeError(f'staged output hash mismatch for {r}: {got} != {w}')
        for r in RELS:
            os.replace(stage/r,paths[r])
    finally:
        shutil.rmtree(stage,ignore_errors=True)
    print('APPLY_FIX331018_OK')
if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: apply-fix331018.py <extension-root>')
    apply(sys.argv[1])

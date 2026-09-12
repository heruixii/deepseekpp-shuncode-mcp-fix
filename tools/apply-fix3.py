from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent
TEMPLATE=SCRIPT_DIR.parent

POLICY_FILE='fix3-policy.js'
SCHEMA_COMPILER=r'''function DPP_SCHEMA_COERCE_1140(e,t){if(!DPP_PLAIN_OBJECT_1140(e))return e;let n=t?.inputSchema?.properties;if(!DPP_PLAIN_OBJECT_1140(n))return e;let r={...e},i=[[`cmd`,`command`],[`timeout`,`timeout_ms`],[`timeoutMs`,`timeout_ms`],[`working_directory`,`cwd`],[`workingDirectory`,`cwd`]];for(let[e,t]of i)if(e in r&&!(t in r)&&Object.prototype.hasOwnProperty.call(n,t)){r[t]=r[e];delete r[e]}for(let[e,t]of Object.entries(n)){if(!DPP_PLAIN_OBJECT_1140(t))continue;if(!(e in r)&&Object.prototype.hasOwnProperty.call(t,`default`))try{r[e]=JSON.parse(JSON.stringify(t.default))}catch{}if(!(e in r))continue;let i=r[e],a=Array.isArray(t.type)?t.type:[t.type];if(typeof i==`string`){if((a.includes(`integer`)||a.includes(`number`))&&i.trim()&&Number.isFinite(Number(i)))r[e]=Number(i);else if(a.includes(`boolean`)&&(i.toLowerCase()===`true`||i.toLowerCase()===`false`))r[e]=i.toLowerCase()===`true`}}return r}'''

def require_once(s,marker,label):
    c=s.count(marker)
    if c!=1: raise RuntimeError(f'{label}: expected exactly one marker, found {c}; target left unchanged')

def replace_once(s,old,new,label):
    require_once(s,old,label)
    return s.replace(old,new,1)

def require_fix2(root):
    required={
      'background.js':['DPP_SAFE_JSON_PARSE_1140','adaptiveMaxDirectTools:5,adaptiveMaxPromptBytes:14e3'],
      'content-scripts/content.js':['DPP_SAFE_JSON_PARSE_1140','DPP_SCHEMA_RAW_KEY_1140'],
      'content-scripts/main-world.js':['DPP_SAFE_JSON_PARSE_1140','DPP_SCHEMA_RAW_KEY_1140'],
    }
    for rel,marks in required.items():
        p=root/rel
        if not p.is_file(): raise RuntimeError(f'missing compatible base file: {rel}')
        s=p.read_text(encoding='utf-8-sig')
        for m in marks:
            if m not in s: raise RuntimeError(f'{rel} is not a Fix2-compatible base (missing {m}); no files changed')

def patch_schema(p):
    s=p.read_text(encoding='utf-8-sig')
    a=s.find('function DPP_SCHEMA_COERCE_1140')
    b=s.find('function DPP_PLAIN_OBJECT_1140',a)
    if a<0 or b<0: raise RuntimeError(f'{p.name}: schema compiler markers missing')
    return s[:a]+SCHEMA_COMPILER+s[b:]

def patch_background(s):
    if not s.startswith('try{importScripts'):
        s='try{importScripts(chrome.runtime.getURL(`fix3-policy.js`))}catch(e){console.error(`[DeepSeek++ Fix3] policy load failed; falling back to Fix2 behavior`,e)}'+s
    old='function Cd(e,t,n,r){let i=Td(`${e.name} ${e.invocationName}`),a=Td(e.title),o=Td(e.description),s=r?1e4:0;t&&(i.includes(t)&&(s+=1e3),a.includes(t)&&(s+=700),o.includes(t)&&(s+=250));for(let e of n)i.includes(e)&&(s+=120),a.includes(e)&&(s+=80),o.includes(e)&&(s+=25);return s}'
    new='function Cd(e,t,n,r){let i=Td(`${e.name} ${e.invocationName}`),a=Td(e.title),o=Td(e.description),s=r?1e4:0;t&&(i.includes(t)&&(s+=1e3),a.includes(t)&&(s+=700),o.includes(t)&&(s+=250));for(let e of n)i.includes(e)&&(s+=120),a.includes(e)&&(s+=80),o.includes(e)&&(s+=25);return s+=(globalThis.DPP_FIX3?.routeBonus?.(e,t)??0)+(globalThis.DPP_FIX3?.recentBonus?.(e)??0),s}'
    if 'globalThis.DPP_FIX3?.routeBonus' not in s: s=replace_once(s,old,new,'routing score')
    old='return mv(i),cv.record({level:u.ok?`info`:`warn`,source:`tool-runtime`,message:`tool finished: ${u.name??d.name} (${u.ok?`ok`:`error`})`,details:DPP_RESULT_DIAG_1140(u)}),u}'
    new='return mv(i),u.ok&&globalThis.DPP_FIX3?.recordSuccess?.(d,f,u),cv.record({level:u.ok?`info`:`warn`,source:`tool-runtime`,message:`tool finished: ${u.name??d.name} (${u.ok?`ok`:`error`})`,details:DPP_RESULT_DIAG_1140(u)}),u}'
    if 'globalThis.DPP_FIX3?.recordSuccess' not in s: s=replace_once(s,old,new,'recent success hook')
    old='p=n=>e.buildPrompt({prompt:n,isFirstMessage:t===null&&r.length===0,messageCount:r.length+1}),m=async(t,n)=>{d(t);let r=await e.executeToolCall(n,{signal:t.controller.signal,assertActive:()=>d(t),trustedCapabilityScopeId:t.capabilityScopeId});if(d(t),!r.ok&&r.error?.details?.externalOutcome===`ambiguous`)throw Error(r.error.message||r.detail||r.summary);return{name:r.name??n.name,provider:r.provider??n.provider,descriptorId:r.descriptorId??n.descriptorId,result:{ok:r.ok,name:r.name,provider:r.provider,descriptorId:r.descriptorId,summary:r.summary,detail:r.detail,output:r.output,truncated:r.truncated,error:r.error}}}'
    new='p=n=>e.buildPrompt({prompt:n,isFirstMessage:t===null&&r.length===0,messageCount:r.length+1}),m=async(t,n)=>{d(t);let i=globalThis.DPP_FIX3?.beforeCall?.(t.dppLoopState,n)??{action:`allow`},r;if(i.action===`stop`)throw Error(i.message);if(i.action===`block`)r=globalThis.DPP_FIX3?.blockedResult?.(n,i.message)??{ok:!1,summary:`Repeated tool loop blocked`,detail:i.message,error:{code:`dpp_fix3_no_progress`,message:i.message,retryable:!1}};else{r=await e.executeToolCall(n,{signal:t.controller.signal,assertActive:()=>d(t),trustedCapabilityScopeId:t.capabilityScopeId});if(d(t),globalThis.DPP_FIX3?.shouldRetry?.(n,r)){await globalThis.DPP_FIX3.retryDelay?.(),d(t);let i=await e.executeToolCall({...n,id:crypto.randomUUID()},{signal:t.controller.signal,assertActive:()=>d(t),trustedCapabilityScopeId:t.capabilityScopeId});globalThis.DPP_FIX3?.noteRetry?.(n,r,i),r=i}}if(d(t),!r.ok&&r.error?.details?.externalOutcome===`ambiguous`)throw Error(r.error.message||r.detail||r.summary);return{name:r.name??n.name,provider:r.provider??n.provider,descriptorId:r.descriptorId??n.descriptorId,result:{ok:r.ok,name:r.name,provider:r.provider,descriptorId:r.descriptorId,summary:r.summary,detail:r.detail,output:r.output,truncated:r.truncated,error:r.error}}}'
    if 'globalThis.DPP_FIX3?.beforeCall' not in s: s=replace_once(s,old,new,'chat policy hook')
    if 'var RF=40;function zF(e){' not in s: s=replace_once(s,'var RF=20;function zF(e){','var RF=40;function zF(e){','step ceiling')
    if 'Math.min(RF,t.dppStepLimit??20)' not in s:
        s=replace_once(s,'for(let r=0;r<RF;r++)','for(let r=0;r<Math.min(RF,t.dppStepLimit??20);r++)','web dynamic step')
        s=replace_once(s,'for(let o=0;o<RF;o++)','for(let o=0;o<Math.min(RF,t.dppStepLimit??20);o++)','api dynamic step')
    if 'dppLoopState:globalThis.DPP_FIX3' not in s:
        s=replace_once(s,'let l={generation:o,capabilityScopeId:crypto.randomUUID(),controller:new AbortController,settled:Promise.resolve()}','let l={generation:o,capabilityScopeId:crypto.randomUUID(),controller:new AbortController,settled:Promise.resolve(),dppStepLimit:globalThis.DPP_FIX3?.stepLimit?.(t.text)??20,dppLoopState:globalThis.DPP_FIX3?.newLoopState?.()??null}','task policy state')
    if 'compactResult?.(e.name,e.result)' not in s:
        a=s.find('function BF('); b=s.find('function VF(',a)
        if a<0 or b<0: raise RuntimeError('BF boundaries missing')
        frag=s[a:b]
        require_once(frag,'JSON.stringify(e.result)','BF result marker')
        s=s[:a]+frag.replace('JSON.stringify(e.result)','JSON.stringify(globalThis.DPP_FIX3?.compactResult?.(e.name,e.result)??e.result)',1)+s[b:]
    old='Y(`TEST_MCP_SERVER_CONNECTION`,async(n,r)=>{let i=await e.refreshMcpServerDiscovery(n.serverId);return await t(r.tabId),{ok:i.health.status===`ready`,cache:i,health:i.health}})'
    new='Y(`TEST_MCP_SERVER_CONNECTION`,async(n,r)=>{let i=await e.refreshMcpServerDiscovery(n.serverId);return await t(r.tabId),{ok:i.health.status===`ready`,cache:i,health:i.health,fix3:globalThis.DPP_FIX3?.healthFromCache?.(i)??null}})'
    if 'healthFromCache?.(i)' not in s: s=replace_once(s,old,new,'health diagnostics')
    needle='extensionVersion:e.getVersion(),entries:cv.snapshot(),parserEntries:t}'
    if 'parserEntries:t,fix3:' not in s: s=replace_once(s,needle,'extensionVersion:e.getVersion(),entries:cv.snapshot(),parserEntries:t,fix3:globalThis.DPP_FIX3?.status?.()??{policyLoaded:!1}}','diagnostic status')
    return s


def patch_content(s):
    helper=r'''function DPP_WEB_BASE_3(e){let t=String(e?.invocationName??e?.name??``).toLowerCase().split(/[.:/]/).pop();return t.replace(/^mcp_+[^_]+_/,``)}function DPP_WEB_SAFE_RETRY_3(e,t){if(t?.ok!==!1||t?.error?.retryable!==!0||t?.error?.details?.externalOutcome===`ambiguous`)return!1;let n=DPP_WEB_BASE_3(e);return!/(run_command|shell_exec|shell_session_exec|apply_patch|write|create|delete|remove|update|edit|patch|move|rename|send|post|put|install|upload|commit|push|merge|execute|exec|run)/.test(n)&&/(read|list|find|search|grep|query|get|status|health|check|stat|snapshot|fetch|lookup|describe|discover|inspect|preview|history)/.test(n)}async function DPP_WEB_RETRY_DELAY_3(){await new Promise(e=>setTimeout(e,220))}'''
    if 'function DPP_WEB_SAFE_RETRY_3' not in s:
        marker='async function DPP_RECORD_PARSE_DIAG_1140(e)'
        require_once(s,marker,'web parse diag marker')
        s=s.replace(marker,helper+marker,1)
    old='if(o){if(jr(i,o)){let e=i.payload?.url;if(typeof e==`string`&&await _2(e)){let e=s2(await o2(i,r));if(e)return e}}return o}'
    new='if(o){if(jr(i,o)){let e=i.payload?.url;if(typeof e==`string`&&await _2(e)){let e=s2(await o2(i,r));if(e)return e}}if(DPP_WEB_SAFE_RETRY_3(i,o)){await DPP_WEB_RETRY_DELAY_3();let e=s2(await o2(i,r));if(e)return e}return o}'
    if 'DPP_WEB_SAFE_RETRY_3(i,o)' not in s: s=replace_once(s,old,new,'web safe retry')
    old='function Fz(e){if(e.length<=4)return e.map(Iz);let t=e.slice(0,-4),n=e.slice(-4);return[...t.map(Lz),...n.map(Iz)]}function Iz(e){return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:e.result.summary,detail:zz(e.result.detail,4e3),error:Rz(e.result.error),output:zz(e.result.output===void 0?void 0:JSON.stringify(e.result.output),8e3),truncated:e.result.truncated===!0}}function Lz(e){return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:zz(e.result.summary,400),error:Rz(e.result.error),windowed:!0,truncated:e.result.truncated===!0}}function Rz(e){if(e)return{code:e.code,message:zz(e.message,400)??``,retryable:e.retryable}}'
    new='function Fz(e){if(e.length<=4)return e.map(Iz);let t=e.slice(0,-4),n=e.slice(-4);return[...t.map(Lz),...n.map(Iz)]}function DPP_MODEL_RESULT_BUDGET_3(e){let t=String(e??``).toLowerCase();return/status|health|check|stat|ping/.test(t)?6e3:/read|list|find|search|grep|snapshot|fetch|get/.test(t)?12e3:/run|exec|shell|build|test/.test(t)?16e3:9e3}function DPP_ERROR_CLASS_3(e){let t=String(e?.code??`unknown`);return t===`dpp_fix3_no_progress`?{stage:`loop_guard`,action:`change_tool_or_parameters`}:/^tool_call_/.test(t)?{stage:`format_or_schema`,action:`repair_parameters`}:/^tool_authorization|authorization/.test(t)?{stage:`authorization`,action:`refresh_authorization`}:/^mcp_(http|sse|connect|initialize|transport|response)/.test(t)?{stage:`mcp_transport`,action:e?.retryable===!0?`safe_retry_if_read_only`:`inspect_connection`}:/^mcp_tool|tool_unsupported/.test(t)?{stage:`mcp_tool`,action:`refresh_tool_catalog`}:{stage:`tool_runtime`,action:e?.retryable===!0?`retry_if_safe`:`inspect_error`}}function Iz(e){let t=e.result.output===void 0?void 0:JSON.stringify(e.result.output),n=DPP_MODEL_RESULT_BUDGET_3(e.name);return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:e.result.summary,detail:zz(e.result.detail,3500),error:Rz(e.result.error),output:zz(t,n),contextCompacted:typeof t==`string`&&t.length>n,truncated:e.result.truncated===!0}}function Lz(e){return{tool:e.name,provider:e.provider?.displayName,ok:e.result.ok,summary:zz(e.result.summary,400),error:Rz(e.result.error),windowed:!0,truncated:e.result.truncated===!0}}function Rz(e){if(e){let t=DPP_ERROR_CLASS_3(e);return{code:e.code,stage:t.stage,action:t.action,message:zz(e.message,400)??``,retryable:e.retryable}}}'
    if 'function DPP_MODEL_RESULT_BUDGET_3' not in s: s=replace_once(s,old,new,'web dynamic result serializer')
    if 'function DPP_STABLE_3' not in s:
        s=replace_once(s,'function Bz(e){return e.descriptors.map(t=>Uz(t,e))}','function Bz(e){let t={last:null,count:0};return e.descriptors.map(n=>Uz(n,e,t))}','web loop state')
        old='function Uz(e,t){let{executeTool:n,callSource:r}=t;return{name:e.invocationName,label:e.title,description:e.description,parameters:e.inputSchema,prepareArguments:e=>e,execute:async(t,i,a,o)=>{let s=await n({id:t,name:e.name,invocationName:e.invocationName,payload:i??{},raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});return{content:[{type:`text`,text:s.result.summary??``}],details:s.result}}}}'
        new='function DPP_STABLE_3(e){if(e===null||typeof e!=`object`)return JSON.stringify(e);if(Array.isArray(e))return`[${e.map(DPP_STABLE_3).join(`,`)}]`;return`{${Object.keys(e).sort().map(t=>`${JSON.stringify(t)}:${DPP_STABLE_3(e[t])}`).join(`,`)}}`}function Uz(e,t,d){let{executeTool:n,callSource:r}=t;return{name:e.invocationName,label:e.title,description:e.description,parameters:e.inputSchema,prepareArguments:e=>e,execute:async(t,i,a,o)=>{let s=`${e.invocationName}:${DPP_STABLE_3(i??{})}`;d.count=d.last===s?d.count+1:1,d.last=s;if(d.count>=4){let t=`Fix3 blocked repeated identical tool call ${d.count}. Change the tool or parameters.`;return{content:[{type:`text`,text:t}],details:{ok:!1,summary:`Repeated tool loop blocked`,detail:t,error:{code:`dpp_fix3_no_progress`,message:t,retryable:!1}}}}let c=await n({id:t,name:e.name,invocationName:e.invocationName,payload:i??{},raw:``,source:{trigger:`agent_run`,requestId:r.requestId,chatSessionId:r.chatSessionId}});return{content:[{type:`text`,text:c.result.summary??``}],details:c.result}}}}'
        s=replace_once(s,old,new,'web identical call guard')
    if 'function Hz(e=``)' not in s:
        s=replace_once(s,'function Hz(){return{maxSteps:25,maxNudges:8,stepTimeoutMs:NR,requestDelayMinMs:PR,requestDelayMaxMs:FR,fullToolResultWindow:4}}','function Hz(e=``){let t=String(e).toLowerCase(),n=/继续.*直到.*完成|直到.*完成|彻底完成|until.*complete|until.*done|finish.*everything/.test(t)?36:/代码|文件|项目|修复|汉化|仓库|构建|测试|code|file|project|fix|repo|build|test/.test(t)?24:12;return{maxSteps:n,maxNudges:8,stepTimeoutMs:NR,requestDelayMinMs:PR,requestDelayMaxMs:FR,fullToolResultWindow:4}}','web dynamic step function')
    if 'Ce=Hz(t.originalPrompt)' not in s:
        s=replace_once(s,'Se=Bz({descriptors:c,executeTool:r,callSource:{requestId:t.capabilityScopeRequestId??`agent:${a}`,chatSessionId:s}}),Ce=Hz(),we=','Se=Bz({descriptors:c,executeTool:r,callSource:{requestId:t.capabilityScopeRequestId??`agent:${a}`,chatSessionId:s}}),Ce=Hz(t.originalPrompt),we=','web dynamic step call')
    if 'b>=Ce.maxSteps&&(ae=$z(d,b))' not in s:
        s=replace_once(s,'ae===null&&ie===null&&g.length>0&&b>=25&&(ae=$z(d,b))','ae===null&&ie===null&&g.length>0&&b>=Ce.maxSteps&&(ae=$z(d,b))','web final budget consistency')
    # Fix 3 continuation hotfix: recognize explicit mid-step text, honor strict-until-complete tasks,
    # allow up to maxNudges consecutive corrections, and reset that counter after a real tool turn.
    if 'function DPP_STRICT_CONTINUATION_31' not in s:
        s=replace_once(s,'function Az(e,t,n){return Sz(n)?!1:n?Mz(jz(n)):!0}',"function DPP_STRICT_CONTINUATION_31(e){let t=String(e??``);return/(?:\\u7ee7\\u7eed(?:\\u6267\\u884c|\\u63a8\\u8fdb|\\u5904\\u7406|\\u505a)?[^\\u3002\\n]{0,24}(?:\\u76f4\\u5230|\\u5230)[^\\u3002\\n]{0,16}\\u5b8c\\u6210|\\u76f4\\u5230[^\\u3002\\n]{0,24}\\u5b8c\\u6210|\\u505a\\u5b8c\\u4e3a\\u6b62|\\u4e00\\u76f4\\u505a\\u5230[^\\u3002\\n]{0,16}\\u5b8c\\u6210|\\u5b8c\\u6210\\u524d[^\\u3002\\n]{0,16}(?:\\u4e0d\\u8981|\\u522b)(?:\\u4e2d\\u65ad|\\u505c\\u6b62|\\u505c)|\\u4e0d\\u8981\\u4e2d\\u65ad(?:\\u4efb\\u52a1)?|until[^.\\n]{0,40}(?:complete|done)|keep\\s+(?:going|working)[^.\\n]{0,40}(?:complete|done)|do\\s+not\\s+stop[^.\\n]{0,40}(?:complete|done))/i.test(t)}function DPP_MIDSTEP_CUE_31(e){let t=String(e??``);return/(?:^|[\\u3002\\uff01\\uff1f.!?\\n;\\uff1b])\\s*(?:\\u5148|\\u63a5\\u7740|\\u7136\\u540e|\\u4e0b\\u4e00\\u6b65|\\u63a5\\u4e0b\\u6765|\\u968f\\u540e|\\u518d|\\u73b0\\u5728)(?:\\u6765|\\u8981|\\u9700\\u8981|\\u5f97|\\u5e94\\u8be5|\\u53ef\\u4ee5|\\u76f4\\u63a5)?\\s*(?:\\u6d4b\\u8bd5|\\u68c0\\u67e5|\\u9a8c\\u8bc1|\\u6267\\u884c|\\u8fd0\\u884c|\\u5199\\u5165|\\u8bfb\\u53d6|\\u641c\\u7d22|\\u67e5\\u627e|\\u6253\\u5f00|\\u4fee\\u6539|\\u66f4\\u65b0|\\u521b\\u5efa|\\u4fdd\\u5b58|\\u5b9a\\u4f4d|\\u786e\\u8ba4|\\u770b\\u770b|\\u8bd5\\u4e00\\u4e0b|\\u8bd5\\u8bd5|\\u5904\\u7406|\\u4fee\\u590d|\\u6784\\u5efa|\\u90e8\\u7f72|\\u63d0\\u4ea4|\\u4e0b\\u8f7d|\\u4e0a\\u4f20|\\u540c\\u6b65|\\u5bfc\\u51fa|\\u8f6c\\u6362|\\u5206\\u6790|\\u5bf9\\u6bd4|\\u7ee7\\u7eed)(?:\\u4e00\\u4e0b|\\u770b\\u770b|\\u5b83|\\u8fd9\\u4e2a|\\u8fd9\\u4e9b|[\\u3002\\uff01!]|$)/i.test(t)||/(?:\\u8fd8\\u9700\\u8981|\\u4ecd\\u9700|\\u9700\\u8981|\\u5f97|\\u5fc5\\u987b|\\u51c6\\u5907|\\u6253\\u7b97|\\u5c06\\u8981|\\u8981)[^\\u3002\\n]{0,36}(?:\\u8c03\\u7528|\\u6267\\u884c|\\u8fd0\\u884c|\\u5199\\u5165|\\u8bfb\\u53d6|\\u6d4b\\u8bd5|\\u68c0\\u67e5|\\u9a8c\\u8bc1|\\u4fee\\u6539|\\u66f4\\u65b0|\\u521b\\u5efa|\\u4fdd\\u5b58|\\u641c\\u7d22|\\u67e5\\u627e|\\u786e\\u8ba4|\\u5904\\u7406|\\u4fee\\u590d|\\u6784\\u5efa|\\u90e8\\u7f72|\\u63d0\\u4ea4|\\u4e0b\\u8f7d|\\u4e0a\\u4f20|\\u540c\\u6b65|\\u5bfc\\u51fa|\\u8f6c\\u6362)/i.test(t)||/(?:^|[.!?\\n;])\\s*(?:(?:first|next|then|now)\\s+(?:i(?:'ll| will)?\\s+)?|(?:i\\s+)?(?:still\\s+)?need(?:s)?\\s+to\\s+)(?:test|check|verify|run|execute|write|read|search|open|update|create|save|inspect|fix|build|deploy|commit|download|upload|sync|export|convert)/i.test(t)}function DPP_NUDGE_LIMIT_31(e,t){return String(e??``).toLowerCase().startsWith(`zh`)?`DeepSeek++ \\u5df2\\u8fde\\u7eed\\u7ea0\\u504f ${t} \\u6b21\\uff0c\\u4f46\\u6a21\\u578b\\u4ecd\\u672a\\u7ed9\\u51fa\\u53ef\\u6267\\u884c\\u5de5\\u5177\\u8c03\\u7528\\u6216 <task_complete> \\u5b8c\\u6210\\u6807\\u8bb0\\u3002\\u5df2\\u5b89\\u5168\\u505c\\u6b62\\u7ea0\\u504f\\u4ee5\\u907f\\u514d\\u7a7a\\u8f6c\\u3002`:`DeepSeek++ corrected ${t} consecutive no-tool replies, but the model still produced neither an executable tool call nor <task_complete>. Stopped safely to avoid a no-progress loop.`}function Az(e,t,n){if(Sz(n))return!1;if(!n)return!0;let r=jz(n);return Mz(r)||DPP_MIDSTEP_CUE_31(r)||DPP_STRICT_CONTINUATION_31(e)}",'continuation intent helpers')
    if 'if(y.currentTurnIsNudge){if(!i)return ie=n,!0;' not in s:
        s=replace_once(s,'shouldStopAfterTurn:({message:e})=>{if(ce=Yz(e),le=e.content.some(e=>e.type===`toolCall`),b>=Ce.maxSteps)return ae===null&&g.length>0&&(ae=$z(d,b)),!0;let n=ce,r=le;if(!m()){if(r)throw Error(Zz(y.currentTurnIsNudge));if(!n.trim())throw Error(`DeepSeek returned an empty agent continuation without a continuable response message.`);return ie=n,!0}if(r)return!1;if(Sz(n))return ie=n,!0;let i=Az(t.originalPrompt,g,Gz(n));return y.currentTurnIsNudge?(i?ae=$z(d,b+1):ie=n,!0):i?!1:(ie=n,!0)},getSteeringMessages:async()=>ue===0?[]:!le&&!y.nudgedInStep&&m()&&!Sz(ce)&&Az(t.originalPrompt,g,Gz(ce))?(y.count+=1,y.nudgedInStep=!0,y.pendingTurn=!0,y.active=!0,y.lastAssistantText=Gz(ce),[{role:`user`,content:Pz(t.originalPrompt,y.lastAssistantText,g,y.count,d),timestamp:Date.now()}]):[]','shouldStopAfterTurn:({message:e})=>{if(ce=Yz(e),le=e.content.some(e=>e.type===`toolCall`),b>=Ce.maxSteps)return ae===null&&g.length>0&&(ae=$z(d,b)),!0;let n=ce,r=le;if(!m()){if(r)throw Error(Zz(y.currentTurnIsNudge));if(!n.trim())throw Error(`DeepSeek returned an empty agent continuation without a continuable response message.`);return ie=n,!0}if(r)return!1;if(Sz(n))return ie=n,!0;let i=Az(t.originalPrompt,g,Gz(n));if(y.currentTurnIsNudge){if(!i)return ie=n,!0;if(y.count>=Ce.maxNudges)return ae=DPP_NUDGE_LIMIT_31(d,y.count),!0;return!1}return i?!1:(ie=n,!0)},getSteeringMessages:async()=>ue===0?[]:y.count>=Ce.maxNudges?[]:!le&&!y.nudgedInStep&&m()&&!Sz(ce)&&Az(t.originalPrompt,g,Gz(ce))?(y.count+=1,y.nudgedInStep=!0,y.pendingTurn=!0,y.active=!0,y.lastAssistantText=Gz(ce),[{role:`user`,content:Pz(t.originalPrompt,y.lastAssistantText,g,y.count,d),timestamp:Date.now()}]):[]','continuation nudge control flow')
    if 'y.nudgedInStep=!1,y.count=0' not in s:
        s=replace_once(s,'g.push(..._),me(),b+=1,x=!0,S=``,ee=``,_.length=0,y.nudgedInStep=!1}','g.push(..._),me(),b+=1,x=!0,S=``,ee=``,_.length=0,y.nudgedInStep=!1,y.count=0}','continuation nudge reset')
    return s

def apply(root):
    root=root.resolve()
    require_fix2(root)
    # Build all in-memory first: fail closed, no partial mutation.
    changes={}
    bg=root/'background.js'
    changes[bg]=patch_background(patch_schema(bg))
    for rel in ['content-scripts/content.js','content-scripts/main-world.js']:
        p=root/rel
        text=patch_schema(p)
        if rel=='content-scripts/content.js': text=patch_content(text)
        changes[p]=text
    import json
    mp=root/'manifest.json'; manifest=json.loads(mp.read_text(encoding='utf-8-sig')); manifest['version_name']=f"{manifest.get('version','unknown')} ShunCode MCP Fix 3"; changes[mp]=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    for rel in ['_locales/en/messages.json','_locales/zh_CN/messages.json']:
        p=root/rel
        if p.exists():
            o=json.loads(p.read_text(encoding='utf-8-sig'))
            if 'extension_name' in o:o['extension_name']['message']='DeepSeek++ ShunCode MCP Fix 3'
            if 'extension_action_title' in o:o['extension_action_title']['message']='DeepSeek++ ShunCode MCP Fix 3'
            changes[p]=json.dumps(o,ensure_ascii=False,indent=2)+'\n'
    policy=(TEMPLATE/POLICY_FILE).read_text(encoding='utf-8-sig')
    changes[root/POLICY_FILE]=policy
    for p,text in changes.items(): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8',newline='')
    md=root/'_metadata'
    if md.exists():
        import shutil; shutil.rmtree(md)
    for legacy in ['README-SHUNCODE-FIX.md','README-SHUNCODE-FIX2.md','FIX2-TEST-REPORT.md']:
        q=root/legacy
        if q.exists(): q.unlink()
    print(f'Fix3 overlay applied safely to {root}')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description='Fail-closed Fix3 overlay for a Fix2-compatible DeepSeek++ bundle.')
    ap.add_argument('target',type=Path)
    args=ap.parse_args()
    apply(args.target)
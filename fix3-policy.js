(()=>{
  const g=globalThis;
  const flags=Object.freeze({
    resultCompaction:true,
    safeRetry:true,
    adaptiveRouting:true,
    recentSuccessBias:true,
    dynamicStepLimit:true,
    loopGuard:true,
    compactErrors:true,
    schemaCompiler:true,
    healthDiagnostics:true,
    delegateLongCommands:true
  });
  const recent=new Map();
  const retryEvents=[];
  const now=()=>Date.now();
  const nameOf=x=>String(x?.invocationName??x?.name??x??``).toLowerCase();
  const baseName=x=>nameOf(x).split(/[.:/]/).pop().replace(/^mcp_+[^_]+_/,``);
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  function trimString(s,max){s=String(s??``);if(s.length<=max)return s;let h=Math.floor(max*.58),t=Math.floor(max*.32);return`${s.slice(0,h)}\n...[DeepSeek++ Fix3 compacted ${s.length-max} chars]...\n${s.slice(-t)}`}
  function jsonLen(v){try{return JSON.stringify(v).length}catch{return 0}}
  function compactValue(v,budget,depth=0){
    if(v==null||typeof v===`number`||typeof v===`boolean`)return v;
    if(typeof v===`string`)return trimString(v,clamp(budget,400,12000));
    if(depth>=4)return `[Fix3: nested value omitted; approx ${jsonLen(v)} chars]`;
    if(Array.isArray(v)){
      if(v.length<=12&&jsonLen(v)<=budget)return v.map(x=>compactValue(x,Math.floor(budget/Math.max(1,v.length)),depth+1));
      let head=v.slice(0,5).map(x=>compactValue(x,Math.floor(budget/12),depth+1));
      let tail=v.slice(-4).map(x=>compactValue(x,Math.floor(budget/12),depth+1));
      return[...head,{__dpp_fix3_omitted_items:Math.max(0,v.length-9)},...tail];
    }
    if(typeof v===`object`){
      let entries=Object.entries(v),out={},per=Math.max(350,Math.floor(budget/Math.max(1,Math.min(entries.length,12))));
      for(let [k,val] of entries.slice(0,30))out[k]=compactValue(val,per,depth+1);
      if(entries.length>30)out.__dpp_fix3_omitted_keys=entries.length-30;
      return out;
    }
    return String(v);
  }
  function modelBudget(tool){let n=baseName(tool);if(/status|health|check|stat|ping/.test(n))return 7000;if(/list|find|search|grep|read|snapshot|fetch|get/.test(n))return 14000;if(/run|exec|shell|build|test/.test(n))return 20000;return 12000}
  function classifyError(err){let c=String(err?.code??`unknown`);if(c===`dpp_fix3_no_progress`)return{stage:`loop_guard`,action:`change_tool_or_parameters`};if(/^mcp_capability_handle_(?:replayed|expired|invalid|descriptor_stale)/.test(c))return{stage:`mcp_capability`,action:`rediscover_capability`};if(/^tool_call_/.test(c))return{stage:`format_or_schema`,action:err?.retryable===true?`repair_and_retry`:`repair_parameters`};if(/^tool_authorization|authorization/.test(c))return{stage:`authorization`,action:`refresh_authorization`};if(/^mcp_(http|sse|connect|initialize|transport|response)/.test(c))return{stage:`mcp_transport`,action:err?.retryable===true?`safe_retry_if_read_only`:`inspect_connection`};if(/^mcp_tool|tool_unsupported/.test(c))return{stage:`mcp_tool`,action:`refresh_tool_catalog`};if(/^background_|runtime_/.test(c))return{stage:`extension_runtime`,action:`inspect_diagnostics`};return{stage:`tool_runtime`,action:err?.retryable===true?`retry_if_safe`:`inspect_error`}}
  function compactError(err){if(!err||typeof err!==`object`)return err;let c=classifyError(err),o=err.details?.externalOutcome,a=o===`ambiguous`;return{code:String(err.code??`unknown`),stage:c.stage,action:a?`verify_before_retry`:c.action,message:trimString(err.message??``,900),retryable:a?false:err.retryable===true,...o?{externalOutcome:o}:{},...a?{retrySafe:false}:{}}}
  function compactResult(tool,result){
    if(!flags.resultCompaction||!result||typeof result!==`object`)return result;
    let budget=modelBudget(tool),out={...result};
    if(typeof out.summary===`string`)out.summary=trimString(out.summary,1200);
    if(typeof out.detail===`string`)out.detail=trimString(out.detail,3600);
    if(out.error)out.error=flags.compactErrors?compactError(out.error):out.error;
    if(out.output!==undefined){let size=jsonLen(out.output);if(size>budget){out.output=compactValue(out.output,budget);out.dppFix3={...(out.dppFix3||{}),resultCompacted:true,originalOutputChars:size,modelBudget:budget,fullResultRetainedInToolHistory:true}}}
    return out;
  }
  const blockedRetry=/(run_command|shell_exec|shell_session_exec|apply_patch|write|create|delete|remove|update|edit|patch|move|rename|send|post|put|install|upload|commit|push|merge|execute|exec|run)/;
  const readRetry=/(read|list|find|search|grep|query|get|status|health|check|stat|snapshot|fetch|lookup|describe|discover|inspect|preview|history)/;
  function shouldRetry(call,result){let n=baseName(call),e=result?.error;if(!flags.safeRetry||result?.ok!==false||e?.retryable!==true)return false;if(e?.details?.externalOutcome===`ambiguous`)return false;if(blockedRetry.test(n))return false;return readRetry.test(n)}
  async function retryDelay(){await new Promise(r=>setTimeout(r,220))}
  function noteRetry(call,first,second){retryEvents.push({ts:now(),tool:baseName(call),first:first?.error?.code??null,secondOk:second?.ok===true});while(retryEvents.length>50)retryEvents.shift()}
  function routeBonus(desc,intent){if(!flags.adaptiveRouting)return 0;let n=baseName(desc),q=String(intent??``).toLowerCase(),b=0;let file=/(?:\u6587\u4ef6|\u76ee\u5f55|\u8bfb\u53d6|\u67e5\u770b|\u641c\u7d22|\u67e5\u627e|file|folder|directory|read|search|find|grep)/i.test(q),note=/(?:obsidian|\u9ed1\u66dc\u77f3|\u7b14\u8bb0|vault)/i.test(q),edit=/(?:\u4fee\u6539|\u7f16\u8f91|\u5199\u5165|\u66ff\u6362|\u8865\u4e01|edit|modify|write|patch|replace)/i.test(q),cmd=/(?:\u547d\u4ee4|\u6267\u884c|\u8fd0\u884c|\u7ec8\u7aef|\u6784\u5efa|\u6d4b\u8bd5|powershell|command|shell|run|exec|build|test)/i.test(q),git=/(?:git|github|\u4ed3\u5e93|\u63d0\u4ea4|\u5206\u652f|commit|branch|repo)/i.test(q);if(file&&/(read|list|find|search|grep|stat|snapshot)/.test(n))b+=650;if(file&&note&&/(run_command|shell|exec|run)/.test(n))b+=850;if(edit&&/(patch|write|edit|replace)/.test(n))b+=800;if(edit&&/(read|find|search|grep)/.test(n))b+=260;if(cmd&&/(run_command|shell|exec|run)/.test(n))b+=900;if(edit&&cmd&&/(run_command|shell|exec|run)/.test(n))b+=400;if(git&&/(git|run_command|shell|exec)/.test(n))b+=620;return b}
  function promptDescriptorCost(desc){if(!desc||typeof desc!==`object`)return 0;let text=[desc.invocationName,desc.title,desc.description].map(x=>String(x??``)).join(`\r\n`),schema;try{schema=JSON.stringify(desc.inputSchema??{})}catch{schema=``}let enc=typeof TextEncoder===`function`?new TextEncoder:null,bytes=x=>enc?enc.encode(x).byteLength:x.length;return bytes(text)+bytes(schema)*2+1024}
  function promptExposureSettings(descriptors,settings,intent){if(!flags.adaptiveRouting||!Array.isArray(descriptors)||!settings||typeof settings!==`object`)return settings;let enabled=descriptors.filter(d=>d?.execution?.enabled!==false),total=enabled.reduce((sum,d)=>sum+promptDescriptorCost(d),0),adaptiveBudget=Number.isInteger(settings.adaptiveMaxPromptBytes)&&settings.adaptiveMaxPromptBytes>0?settings.adaptiveMaxPromptBytes:14000,triggerBudget=Math.max(28000,adaptiveBudget*2);if(total<=triggerBudget)return settings;let servers=settings.servers&&typeof settings.servers===`object`&&!Array.isArray(settings.servers)?settings.servers:{},nextServers={...servers},changed=!1;for(let d of enabled){if(d?.provider?.kind!==`mcp`||!d.provider.id)continue;let id=d.provider.id,current=servers[id],mode=current?.mode??`direct`;if(mode!==`direct`)continue;nextServers[id]={mode:`adaptive`,pinnedDescriptorIds:Array.isArray(current?.pinnedDescriptorIds)?[...current.pinnedDescriptorIds]:[]},changed=!0}return changed?{...settings,servers:nextServers}:settings}
  function recordSuccess(call,desc,result){if(!flags.recentSuccessBias||result?.ok!==true)return;let n=baseName(desc??call);recent.set(n,{ts:now(),count:(recent.get(n)?.count??0)+1})}
  function recentBonus(desc){if(!flags.recentSuccessBias)return 0;let r=recent.get(baseName(desc));if(!r)return 0;let age=now()-r.ts;if(age>10*60*1000){recent.delete(baseName(desc));return 0}return Math.min(420,120+r.count*45)}
  function stepLimit(text){if(!flags.dynamicStepLimit)return 20;let q=String(text??``).toLowerCase();if(/^\s*(?:\u7ee7\u7eed|\u63a5\u7740|\u7ee7\u7eed\u5427|\u7ee7\u7eed\u6267\u884c|continue|go\s+on|carry\s+on)\s*[\u3002.!\uff01\uff1f?]*\s*$/i.test(q)||/(?:\u7ee7\u7eed.*(?:\u76f4\u5230|\u5230).*\u5b8c\u6210|\u76f4\u5230.*\u5b8c\u6210|\u5f7b\u5e95\u5b8c\u6210|until.*complete|until.*done|finish.*everything)/i.test(q))return 128;if(/(?:\u4ee3\u7801|\u6587\u4ef6|\u9879\u76ee|\u4fee\u590d|\u6c49\u5316|\u4ed3\u5e93|\u6784\u5efa|\u6d4b\u8bd5|code|file|project|fix|repo|build|test)/i.test(q))return 96;return 88}
  function stable(v){if(v===null||typeof v!==`object`)return JSON.stringify(v);if(Array.isArray(v))return`[${v.map(stable).join(`,`)}]`;return`{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${stable(v[k])}`).join(`,`)}}`}
  function newLoopState(){return{last:null,count:0,blocked:0}}
  function beforeCall(state,call){if(!flags.loopGuard||!state)return{action:`allow`};let sig=`${baseName(call)}:${stable(call?.payload??{})}`;state.count=state.last===sig?state.count+1:1;state.last=sig;if(state.count>=6)return{action:`stop`,message:`Fix3 stopped a repeated identical tool loop after ${state.count} attempts. Choose a different tool or parameters.`};if(state.count>=4){state.blocked++;return{action:`block`,message:`Fix3 blocked repeated identical tool call ${state.count}. Change the tool or parameters instead of repeating the same call.`}}return{action:`allow`}}
  function blockedResult(call,message){return{ok:false,name:call?.name,provider:call?.provider,descriptorId:call?.descriptorId,summary:`Repeated tool loop blocked`,detail:message,error:{code:`dpp_fix3_no_progress`,message,retryable:false},truncated:false}}
  function longCommandInfo(call){let n=baseName(call),c=typeof call?.payload?.command===`string`?call.payload.command:``;return /run_command|shell_exec|shell_session_exec/.test(n)&&c.length>=6000?{delegatedToShunCode:true,chars:c.length,reason:`ShunCode script_bridge already handles long Windows commands; Fix3 intentionally does not duplicate this layer.`}:null}
  function healthFromCache(cache){let ds=Array.isArray(cache?.descriptors)?cache.descriptors:[],names=ds.map(baseName),run=ds.find(d=>/run_command/.test(baseName(d))),props=run?.inputSchema?.properties??{};return{policyLoaded:true,ready:cache?.health?.status===`ready`,toolCount:ds.length,hasRunCommand:!!run,hasApplyPatch:names.some(n=>/apply_patch/.test(n)),runCommandSchemaOk:!!run&&typeof props===`object`&&!!props.command,longCommandHandling:`delegated_to_shuncode_script_bridge`,resultCompaction:`model_context_only_full_history_preserved`}}
  function status(){return{version:3,flags,recentTools:[...recent.entries()].map(([tool,v])=>({tool,ageMs:now()-v.ts,count:v.count})).slice(-20),retryEvents:[...retryEvents],longCommandHandling:`delegated_to_shuncode_script_bridge`}}
  g.DPP_FIX3=Object.freeze({flags,compactResult,modelBudget,classifyError,shouldRetry,retryDelay,noteRetry,routeBonus,promptDescriptorCost,promptExposureSettings,recordSuccess,recentBonus,stepLimit,newLoopState,beforeCall,blockedResult,longCommandInfo,healthFromCache,status});
})();
function DPP_BUDGET_DESCRIPTORS_331048(list){
  // Size is characters, NOT tokens. Preserve tool identity, required fields and validation constraints.
  try{return JSON.stringify(list).length>16000?DPP_COMPACT_DESCRIPTORS_331020(list):list}catch{return list}
}
function DPP_SEARCH_CALL_331048(call){
  if(DPP_TOOL_NAME_33(call?.invocationName??call?.name)!==`search_files`)return call;
  const d=DPP_COMMON_DESCRIPTOR_33(call);
  if(d?.provider?.kind!==`mcp`||d?.inputSchema?.properties?.exclude?.type!==`array`||!call.payload||typeof call.payload!==`object`||Array.isArray(call.payload))return call;
  if(call.payload.exclude!==undefined&&!Array.isArray(call.payload.exclude))return call;
  const excludes=[...new Set([...(call.payload.exclude??[]),`[Nn][Uu][Ll]`,`**/[Nn][Uu][Ll]`])];
  return {...call,payload:{...call.payload,exclude:excludes},dppSearchExcludes331048:true};
}
function DPP_SEARCH_RESULT_331048(call,result){
  if(!result||!call?.dppSearchExcludes331048)return result;
  const note=`Search scope excludes Windows NUL device-name entries (case-insensitive), in addition to the requested exclusions. These entries were not searched; no files were deleted.`;
  return {...result,detail:[result.detail,note].filter(Boolean).join(`\n`)};
}
function DPP_TRACE_COUNTS_331048(trace){
  const steps=Array.isArray(trace.steps)?trace.steps:[];
  return {...trace,totalTools:Math.max(trace.totalTools||0,(trace.initialExecutions?.length||0)+steps.reduce((n,s)=>n+(s.toolExecutions?.length||0),0)),totalSteps:Math.max(trace.totalSteps||0,...steps.map(s=>s.index+1))};
}
function DPP_TRACE_NEWER_331048(old,next){
  if(!old)return next;
  if(old.loopId!==next.loopId)return Number(next.createdAt)>Number(old.createdAt)?next:old;
  // A stale or repaired UI snapshot must never replace a newer execution checkpoint.
  if(Number(next.updatedAt)<Number(old.updatedAt))return old;
  if(old.dppWriter331048&&next.dppWriter331048!==old.dppWriter331048)return old;
  if(old.dppWriter331048===next.dppWriter331048 && (old.dppRevision331048||0)>(next.dppRevision331048||0))return old;
  const steps=new Map((old.steps??[]).map(s=>[s.index,s]));
  for(const step of next.steps??[]){const prev=steps.get(step.index);if(!prev||(prev.toolExecutions?.length||0)<=(step.toolExecutions?.length||0))steps.set(step.index,step)}
  return DPP_TRACE_COUNTS_331048({...next,steps:[...steps.values()].sort((a,b)=>a.index-b.index)});
}
function DPP_TRACE_LOCK_331048(fn){
  if(typeof navigator!==`undefined`&&navigator.locks?.request)return navigator.locks.request(`dpp-inline-traces-331048`,fn);
  return fn();
}
function DPP_TRACE_TOOL_331048(trace,event){
  if(!event.execution)return trace;
  const step=trace.steps.find(s=>s.index===event.stepIndex),items=[...(step?.toolExecutions??[])],x=event.execution;
  const id=x.callId??x.call?.id;
  const i=id==null?-1:items.findIndex(y=>(y.callId??y.call?.id)===id);
  if(i>=0)items[i]=x;else items.push(x);
  return DPP_TRACE_COUNTS_331048({...T0(trace,event.stepIndex,{status:`executing_tools`,toolExecutions:items}),dppPendingCalls331048:(trace.dppPendingCalls331048??[]).filter(x=>x!==id)});
}
function DPP_TRACE_DIAG_331048(stage,trace,error){
  try{
    const key=`dpp_trace_write_diag_331048`,raw=JSON.parse(localStorage.getItem(key)||`[]`),rows=Array.isArray(raw)?raw:[];
    rows.push({stage,time:Date.now(),id:String(trace.id??``).slice(0,120),loopId:String(trace.loopId??``).slice(0,120),writer:String(trace.dppWriter331048??``).slice(0,80),revision:trace.dppRevision331048??null,status:trace.status,stopReason:trace.dppStopReason331048??null,totalSteps:trace.totalSteps,totalTools:trace.totalTools,pendingCalls:trace.dppPendingCalls331048?.length??0,errorName:error?String(error.name??`Error`).slice(0,80):null});
    localStorage.setItem(key,JSON.stringify(rows.slice(-64)));
  }catch{}
}

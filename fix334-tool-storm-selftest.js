const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
let pass=0; function ok(v,m){if(!v){console.error('FAIL',m);process.exit(1)}pass++;console.log('PASS',m)}
function between(s,a,b){const i=s.indexOf(a);if(i<0)throw Error('missing '+a);const j=s.indexOf(b,i);if(j<0)throw Error('missing '+b);return s.slice(i,j)}
const manual=between(content,'var DPP_MANUAL_TOOL_LIMIT_334=8','async function _Z(');
const ctx={Map,Set,String,Date,Number,Promise,Object,Array,console,window:{addEventListener(){}},setTimeout(){return 1},clearTimeout(){}};ctx.DPP_TOOL_NAME_33=e=>String(e??'').toLowerCase().split(/[.:/]/).pop().replace(/^mcp_+[^_]+_/,'');vm.createContext(ctx);vm.runInContext(manual+';globalThis.g=DPP_MANUAL_GATE_334;globalThis.s=DPP_MANUAL_STARTED_334;globalThis.c=DPP_MANUAL_CHUNK_334;globalThis.f=DPP_MANUAL_FINISH_334;globalThis.state=DPP_MANUAL_TOOL_STATE_334;',ctx);
function call(id,name='run_command',req='r1',trigger='manual_chat'){return{id,name,invocationName:name,payload:{command:'echo '+id,background:false},source:{trigger,requestId:req}}}
let allowed=0,blocked=0,first=0;
for(let i=0;i<228;i++){const r=ctx.g(call('c'+i)); if(r.allow)allowed++; else{blocked++; if(r.first)first++;}}
ok(allowed===6,'228 same-tool storm allows only first 6');
ok(blocked===222,'remaining 222 calls blocked before execution');
ok(first===1,'storm emits one first-block signal');
ok(ctx.state.get('r1').blocked===true,'request remains circuit-broken');
ok(ctx.s(call('late-start'))===false,'later TOOL_CALL_STARTED suppressed');
ok(ctx.c({requestId:'r1',id:'c0'})===true,'chunks for an already allowed call still pass');
ok(ctx.c({requestId:'r1',id:'new-blocked'})===false,'chunks for later blocked calls suppressed');
ok(ctx.f('r1').blocked===true && !ctx.state.has('r1'),'response finish clears breaker state');
// Mixed-tool total limit.
for(let i=0;i<8;i++) ok(ctx.g(call('m'+i,'tool_'+i,'r2')).allow===true,'mixed call '+(i+1)+' within total budget');
ok(ctx.g(call('m8','tool_8','r2')).allow===false,'9th mixed tool blocked by total budget');ctx.f('r2');
// Agent calls bypass manual-chat gate entirely.
for(let i=0;i<40;i++) ok(ctx.g(call('a'+i,'run_command','agentreq','agent_run')).allow===true,'agent_run bypass '+i);
ok(!ctx.state.has('agentreq'),'agent_run does not allocate manual breaker state');
// Duplicate call id is not executed twice.
ok(ctx.g(call('d1','run_command','r3')).allow===true,'first id allowed');let dup=ctx.g(call('d1','run_command','r3'));ok(dup.allow===false&&dup.duplicate===true,'duplicate call id blocked');ctx.f('r3');
// Command sanity helper from production source.
const san=between(content,'function DPP_COMMAND_SANITY_334','function DPP_COMMON_PREFLIGHT_33');const c2={Number,String};c2.DPP_TOOL_NAME_33=e=>String(e??'').toLowerCase().split(/[.:/]/).pop();vm.createContext(c2);vm.runInContext(san+';globalThis.sanity=DPP_COMMAND_SANITY_334;',c2);
ok(c2.sanity('run_command',{command:"Get-ChildItem 'D:\\' | Out-String -Width 83076749736557242056487941267521536000000"})!==null,'observed pathological -Width blocked');
ok(c2.sanity('run_command',{command:"Get-ChildItem 'D:\\' | Out-String -Width 4096"})===null,'reasonable -Width allowed');
ok(c2.sanity('read_files',{path:'x'})===null,'non-command tool unaffected');
// Background safety net.
const m=bg.match(/function DPP_AUTH_CALL_LIMIT_334\(e\)\{[^}]+\}/);ok(!!m,'background call-limit helper present');const bctx={};vm.createContext(bctx);vm.runInContext(m[0]+';globalThis.l=DPP_AUTH_CALL_LIMIT_334;',bctx); // pa is free var; inject via source instead
// Re-evaluate with pa in same lexical context.
const bctx2={};vm.createContext(bctx2);vm.runInContext('var pa=128;'+m[0]+';globalThis.l=DPP_AUTH_CALL_LIMIT_334;',bctx2);
ok(bctx2.l({trigger:'manual_chat'})===24,'manual_chat background safety limit 24');
ok(bctx2.l({trigger:'sidepanel_chat'})===24,'sidepanel background safety limit 24');
ok(bctx2.l({trigger:'test'})===8,'test safety limit 8');
ok(bctx2.l({trigger:'agent_run'})===128,'agent_run keeps 128-call capacity');
// Wiring/static invariants.
ok(content.includes('case`TOOL_CALL`:{let t=S1(e.data),n=DPP_MANUAL_GATE_334(t);if(!n.allow){DPP_MANUAL_DROP_334(t,n);break}'),'gate runs before x1 execution');
ok(content.includes('a?.blocked||J$(t,i)'),'stormed response cannot auto-start inline agent');
ok(content.includes('case`REQUEST_TERMINAL`:{let t=e.payload?.requestId;if(typeof t!=`string`)break;')&&content.includes('DPP_MANUAL_FINISH_334(t),jJ.has(t)||MJ.has(t)'),'terminal path clears breaker');
ok(bg.split('Object.keys(a.calls).length>=DPP_AUTH_CALL_LIMIT_334(a)').length-1===2,'both authorization reservation paths use trigger-aware safety net');
ok(content.includes('dpp_tool_storm_blocked')&&content.includes('dpp_tool_parameter_unsafe'),'new errors classified explicitly');
// Hard-limit recovery must not recommend re-authorization.
const clsSrc=between(content,'function DPP_ERROR_CLASS_3','function DPP_CAPABILITY_WINDOW_32');const ectx={String};vm.createContext(ectx);vm.runInContext(clsSrc+';globalThis.cls=DPP_ERROR_CLASS_3;',ectx);let cls=ectx.cls({code:'tool_authorization_call_limit',retryable:false});ok(cls.stage==='tool_storm_guard'&&cls.action==='stop_tool_calls_and_summarize','authorization call limit is terminal, not refreshable');
ok(content.includes('async read(){return DPP_TRACE_LOCK_331048(()=>wi(async()=>{let e=await t.readAlreadyLocked(),n=DPP_TRIM_AGENT_TRACES_333(e);return n.length!==e.length&&await t.writeAfterReadAlreadyLocked(n),n}))}'),'stale oversized traces are trimmed on read under lock');
ok(content.includes('ZV(),await jX(),JX(k0()),t()&&'),'runtime-state startup triggers stale trace migration');
console.log(`FIX334_TOOL_STORM_PASS ${pass}/${pass}`);
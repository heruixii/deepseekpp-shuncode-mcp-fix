const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
const src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
let pass=0,fail=0;function t(n,c,d=''){console.log(`${c?'PASS':'FAIL'} ${n}${d?' '+d:''}`);c?pass++:fail++}
function between(a,b){const i=src.indexOf(a),j=src.indexOf(b,i+a.length);if(i<0||j<0)throw Error('range missing '+a+' -> '+b);return src.slice(i,j)}
const code=between('function DPP_MCP_TRANSIENT_VERIFICATION_33107','function Uz(');
const ctx={String,Promise,setTimeout,clearTimeout};ctx.DPP_TOOL_EFFECT_31=(name,payload)=>payload?.effect||(['find_files','read_files','search_files','list_directory'].includes(name)?'verification':'neutral');vm.createContext(ctx);vm.runInContext(code+';Object.assign(globalThis,{tr:DPP_MCP_TRANSIENT_VERIFICATION_33107,delay:DPP_MCP_RETRY_DELAY_33107});',ctx);
const err=(status,retryable=true)=>({ok:false,error:{code:'mcp_http_error',message:`MCP server returned HTTP ${status}.`,retryable}});
t('503 verification retryable',ctx.tr('find_files',{},err(503))===true);
t('502 verification retryable',ctx.tr('read_files',{},err(502))===true);
t('504 verification retryable',ctx.tr('search_files',{},err(504))===true);
t('500 excluded by narrow policy',ctx.tr('find_files',{},err(500))===false);
t('nonretryable excluded',ctx.tr('find_files',{},err(503,false))===false);
t('mutation excluded',ctx.tr('run_command',{effect:'mutation'},err(503))===false);
t('neutral excluded',ctx.tr('run_command',{effect:'neutral'},err(503))===false);
t('non-mcp code excluded',ctx.tr('find_files',{}, {ok:false,error:{code:'tool_error',message:'HTTP 503',retryable:true}})===false);
(async()=>{
 const ac=new AbortController();ac.abort();t('pre-aborted delay cancels',await ctx.delay(ac.signal,5)===false);
 const ac2=new AbortController();setTimeout(()=>ac2.abort(),5);t('mid-delay abort cancels',await ctx.delay(ac2.signal,50)===false);
 t('healthy delay completes',await ctx.delay(undefined,1)===true);
 t('retry wiring has unique id',src.includes(':dpp33107-mcp-retry`'));
 t('retry happens before PTY direct fallback',src.indexOf('DPP_MCP_TRANSIENT_VERIFICATION_33107(e.invocationName,c,f?.result)')<src.indexOf('DPP_SHOULD_DIRECT_RETRY_33(e.invocationName,c,f?.result)'));
 t('retry reuses same payload only after safe classifier',src.includes('DPP_MCP_TRANSIENT_VERIFICATION_33107(e.invocationName,c,f?.result)&&await DPP_MCP_RETRY_DELAY_33107(a)'));
 t('manual request abort helper present',src.includes('function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;return r1(),!0}'));
 const bz=between('async function bZ(e)','function xZ(e)');
 t('manual request aborts after valid body parse',bz.includes('let o=Kc(e.route,e.body);if(!o){xZ(t);return}DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107();'));
 t('abort happens before manual authorization',bz.indexOf('DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107();')<bz.indexOf('jZ({requestId:i,trigger:`manual_chat`'));
 t('existing agent budget preserved',src.includes('DPP_AGENT_MIN_BUDGET_338=88,DPP_AGENT_PROJECT_BUDGET_338=96,DPP_AGENT_COMPLETION_BUDGET_338=128'));
 t('existing direct retry mutation guard preserved',src.includes('DPP_TOOL_EFFECT_31(`run_command`,t)===`verification`&&DPP_PTY_EMPTY_33(n)'));
 // Execute the production Uz wrapper with mocks: retry exactly once for safe transient reads,
 // never replay mutations, and never retry after cancellation.
 const uzSrc=between('function Uz(e,t,d)','var Wz=');
 const wctx={String,JSON,Promise};
 wctx.DPP_STABLE_3=x=>JSON.stringify(x);
 wctx.DPP_REQUIRED_ARGS_33=()=>[];
 wctx.DPP_WINDOWS_ENCODING_GUARD_33=()=>null;
 wctx.DPP_TOOL_EFFECT_31=(name,payload)=>name==='find_files'?'verification':name==='run_command'&&/Set-Content/i.test(String(payload?.command||''))?'mutation':'neutral';
 wctx.DPP_MCP_TRANSIENT_VERIFICATION_33107=(name,payload,result)=>result?.ok===false&&result?.error?.code==='mcp_http_error'&&result?.error?.retryable===true&&/HTTP\s+(?:502|503|504)\b/i.test(result?.error?.message||'')&&wctx.DPP_TOOL_EFFECT_31(name,payload)==='verification';
 wctx.DPP_MCP_RETRY_DELAY_33107=async signal=>!signal?.aborted;
 wctx.DPP_SHOULD_DIRECT_RETRY_33=()=>false;
 wctx.DPP_DESCRIPTOR_PROPERTY_33108=(descriptor,name)=>!!descriptor?.inputSchema?.properties&&Object.prototype.hasOwnProperty.call(descriptor.inputSchema.properties,name);
 vm.createContext(wctx);vm.runInContext(uzSrc+';globalThis.Uz=Uz;',wctx);
 const desc=n=>({invocationName:n,name:n,title:n,description:n,inputSchema:{type:'object'}});
 async function runWrap(name,payload,responses,signal){const calls=[];const tool=wctx.Uz(desc(name),{executeTool:async c=>{calls.push(c);return{name,result:responses.shift()}},callSource:{requestId:'req',chatSessionId:'chat'}},{last:null,count:0});const out=await tool.execute('call1',payload,signal,()=>{});return{calls,out}}
 let sim=await runWrap('find_files',{patterns:['x']},[err(503),{ok:true,summary:'ok'}],new AbortController().signal);
 t('wrapper retries safe 503 exactly once',sim.calls.length===2&&sim.calls[1].id==='call1:dpp33107-mcp-retry',JSON.stringify(sim.calls.map(x=>x.id)));
 t('wrapper returns retry result',sim.out.details?.ok===true&&sim.out.details?.summary==='ok');
 sim=await runWrap('run_command',{command:"Set-Content -Path x.txt -Value hi",background:false},[err(503),{ok:true,summary:'should-not-run'}],new AbortController().signal);
 t('wrapper never retries mutation 503',sim.calls.length===1,JSON.stringify(sim.calls.map(x=>x.id)));
 const ac3=new AbortController();ac3.abort();sim=await runWrap('find_files',{patterns:['x']},[err(503),{ok:true,summary:'should-not-run'}],ac3.signal);
 t('wrapper abort blocks second MCP call',sim.calls.length===1,JSON.stringify(sim.calls.map(x=>x.id)));
 const hctx={calls:0,t1:()=>true,r1:()=>{hctx.calls++}};vm.createContext(hctx);vm.runInContext('function DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107(){if(!t1())return!1;return r1(),!0};globalThis.h=DPP_ABORT_ACTIVE_AGENT_FOR_MANUAL_REQUEST_33107;',hctx);t('manual supersede helper aborts active agent once',hctx.h()===true&&hctx.calls===1);
 if(fail){console.error(`FIX33107_FAIL pass=${pass} fail=${fail}`);process.exit(1)}console.log(`FIX33107_PASS ${pass}/${pass+fail}`);
})().catch(e=>{console.error(e);process.exit(1)});

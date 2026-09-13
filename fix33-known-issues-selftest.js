const fs=require('fs'), path=require('path'), vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
let fail=0, pass=0;
function t(name,got,want){const ok=typeof want==='function'?want(got):Object.is(got,want);console.log((ok?'PASS':'FAIL')+' '+name+' got='+JSON.stringify(got));if(ok)pass++;else fail++;}
function range(a,b){const i=source.indexOf(a),j=source.indexOf(b,i+a.length);if(i<0||j<0)throw new Error('range missing '+a+' -> '+b);return source.slice(i,j);}
function load(code, exports, extra={}){const ctx={console,AbortController,DOMException,setTimeout,clearTimeout,Promise,JSON,String,Object,Array,RegExp,Number,Math,...extra};vm.createContext(ctx);vm.runInContext(code+'\n;Object.assign(globalThis,{'+exports.map(x=>x+':'+x).join(',')+'});',ctx);return ctx;}

// 1. Stream finish compatibility and privacy-limited diagnostics.
let stream=load(range('function DPP_STREAM_DIAG_FRAME_33','function wI(')+range('function DPP_STREAM_FINISHED_33','function WI('),['DPP_STREAM_DIAG_FRAME_33','DPP_STREAM_DIAG_PUSH_33','DPP_STREAM_FINISHED_33','UI']);
t('finish-direct',stream.UI({p:'response/status',v:'FINISHED'}),true);
t('finish-direct-quasi',stream.UI({p:'quasi_status',v:'FINISHED'}),true);
t('finish-nested-batch-response-status',stream.UI({o:'BATCH',v:[{p:'response/content',v:'x'},{p:'response/status',v:'FINISHED'}]}),true);
t('finish-deep-nested',stream.UI({payload:{response:{o:'BATCH',v:[{p:'quasi_status',v:'FINISHED'}]}}}),true);
t('finish-not-content-string',stream.UI({p:'response/content',v:'FINISHED'}),false);
t('finish-not-other-status',stream.UI({p:'response/status',v:'RUNNING'}),false);
const diag=stream.DPP_STREAM_DIAG_FRAME_33({p:'response/content',o:'APPEND',v:'TOP_SECRET_TEXT'},{type:'message'});
t('diag-no-content',JSON.stringify(diag).includes('TOP_SECRET_TEXT'),false);
const diag2=stream.DPP_STREAM_DIAG_FRAME_33({o:'BATCH',v:[{p:'response/status',v:'FINISHED'},{p:'response/content',v:'SECRET'}]},{type:'message'});
t('diag-keeps-status',diag2.batch?.[0]?.v,'FINISHED');
t('diag-drops-batch-content',JSON.stringify(diag2).includes('SECRET'),false);

// 2. Safe incomplete-stream retry: only empty/no-id EOF is replayed.
const hrCode=range('async function HR(','function UR(');
async function runHr(sequence){let calls=0;const ctx=load(hrCode,['HR'],{
 zR:2,
 IR:()=>({signal:new AbortController().signal,clear(){},timedOut:()=>false}),
 LR:async()=>{},
 WL:async(e,handlers)=>{const item=sequence[calls++];if(item.throw)throw item.throw;if(item.text)handlers.onTextChunk(item.text,item.text);if(item.reasoning)handlers.onReasoningChunk(item.reasoning,item.reasoning);return {assistantText:'',responseMessageId:item.responseMessageId??null,requestMessageId:item.requestMessageId??null,finished:!!item.finished,dppStreamEvents:item.events??[]};}
 });
 const out=await ctx.HR({}, {onTextChunk(){},onReasoningChunk(){}}, new AbortController().signal);return {calls,out};
}
(async()=>{
 let r=await runHr([{finished:false},{finished:true,responseMessageId:9,events:[{p:'response/status',v:'FINISHED'}]}]);t('stream-empty-eof-retried-once',r.calls,2);t('stream-empty-eof-retry-finishes',r.out.finished,true);
 r=await runHr([{finished:false,text:'partial'},{finished:true}]);t('stream-partial-not-retried',r.calls,1);t('stream-partial-remains-incomplete',r.out.finished,false);
 r=await runHr([{finished:false,responseMessageId:88},{finished:true}]);t('stream-id-not-retried',r.calls,1);

 // 3. Tool safety helpers / classification.
 const effectCode=range('function DPP_TOOL_EFFECT_31(','function DPP_COMPLETION_GATE_31(');
 const izCode=range('function DPP_TOOL_NAME_33','function Rz(');
 const helper=load(effectCode+izCode,['DPP_TOOL_EFFECT_31','DPP_TOOL_NAME_33','DPP_RESULT_HINT_33'],{
   DPP_TOOL_BASE_31:e=>String(e??'').toLowerCase().split(/[.:/]/).pop(),
   DPP_CAPABILITY_WINDOW_32:()=>null,DPP_MODEL_RESULT_BUDGET_3:()=>9000,zz:(e)=>e,Rz:e=>e
 });
 t('effect-writealltext-mutation',helper.DPP_TOOL_EFFECT_31('run_command',{command:'[IO.File]::WriteAllText($p,$x,$enc)'}),'mutation');
 t('effect-getcontent-verification',helper.DPP_TOOL_EFFECT_31('run_command',{command:'Get-Content x.txt -Raw'}),'verification');
 t('tool-name-namespaced-run',helper.DPP_TOOL_NAME_33('mcp_t_abc_run_command'),'run_command');
 let hint=helper.DPP_RESULT_HINT_33({name:'read_files',result:{error:{code:'FILE_NOT_FOUND'}}});t('workspace-hint-present',typeof hint.recoveryHint==='string',true);
 t('workspace-hint-not-run-command','recoveryHint' in helper.DPP_RESULT_HINT_33({name:'run_command',result:{error:{code:'FILE_NOT_FOUND'}}}),false);

 const uzCode=range('function DPP_REQUIRED_ARGS_33','var Wz=');
 const ctx=load(effectCode+izCode+uzCode,['DPP_REQUIRED_ARGS_33','DPP_WINDOWS_ENCODING_GUARD_33','DPP_PTY_EMPTY_33','DPP_SHOULD_DIRECT_RETRY_33','Uz'],{
   DPP_TOOL_BASE_31:e=>String(e??'').toLowerCase().split(/[.:/]/).pop(),
   DPP_CAPABILITY_WINDOW_32:()=>null,DPP_MODEL_RESULT_BUDGET_3:()=>9000,zz:e=>e,Rz:e=>e,
   DPP_STABLE_3:e=>JSON.stringify(e)
 });
 const desc={name:'run_command',invocationName:'run_command',title:'run',description:'run',inputSchema:{type:'object',required:['command','background'],properties:{command:{type:'string'},background:{type:'boolean'},execution:{type:'string'}}}};
 t('missing-args',Array.from(ctx.DPP_REQUIRED_ARGS_33(desc,{})).sort().join(','),'background,command');
 const dangerous=`$rc=Get-Content $r -Raw\n$rc=$rc -replace 'a','b'\n[System.IO.File]::WriteAllText($r,$rc,$enc)`;
 t('utf8-danger-blocked',typeof ctx.DPP_WINDOWS_ENCODING_GUARD_33('run_command',{command:dangerous})==='string',true);
 t('utf8-explicit-safe',ctx.DPP_WINDOWS_ENCODING_GUARD_33('run_command',{command:`$rc=Get-Content $r -Raw -Encoding UTF8\n[IO.File]::WriteAllText($r,$rc,$enc)`}),null);
 t('utf8-readonly-safe',ctx.DPP_WINDOWS_ENCODING_GUARD_33('run_command',{command:'Get-Content $r -Raw'}),null);
 const ptyEmpty={ok:true,summary:'ok',detail:'status: completed\nexecution: pty\nexit_code: 0\ntotal_output_bytes: 0',output:[]};
 t('pty-empty-detected',ctx.DPP_PTY_EMPTY_33(ptyEmpty),true);
 t('pty-read-direct-retry',ctx.DPP_SHOULD_DIRECT_RETRY_33('run_command',{command:'Get-Content x.txt -Raw',background:false},ptyEmpty),true);
 t('pty-mutation-no-retry',ctx.DPP_SHOULD_DIRECT_RETRY_33('run_command',{command:'Set-Content x.txt ok',background:false},ptyEmpty),false);
 t('pty-direct-no-retry',ctx.DPP_SHOULD_DIRECT_RETRY_33('run_command',{command:'Get-Content x.txt -Raw',background:false,execution:'direct'},ptyEmpty),false);

 let calls=[];let wrapper=ctx.Uz(desc,{executeTool:async c=>{calls.push(c);return{result:{ok:true,summary:'ok',detail:'status: completed\nexecution: pty\nexit_code: 0\ntotal_output_bytes: 0',output:[]}}},callSource:{requestId:'r',chatSessionId:'s'}},{last:null,count:0});
 let res=await wrapper.execute('id1',{});t('empty-args-local-block',res.details.error.code,'dpp_tool_arguments_missing');t('empty-args-no-mcp-call',calls.length,0);
 calls=[];wrapper=ctx.Uz(desc,{executeTool:async c=>{calls.push(c);return{result:{ok:true,summary:'ok'}}},callSource:{requestId:'r',chatSessionId:'s'}},{last:null,count:0});
 res=await wrapper.execute('id2',{command:dangerous,background:false});t('dangerous-command-local-block',res.details.error.code,'dpp_windows_text_encoding_unsafe');t('dangerous-command-no-mcp-call',calls.length,0);
 calls=[];wrapper=ctx.Uz(desc,{executeTool:async c=>{calls.push(c);if(c.payload.execution==='direct')return{result:{ok:true,summary:'direct-ok',detail:'status: completed\nexecution: direct\nexit_code: 0\ntotal_output_bytes: 15'}};return{result:ptyEmpty}},callSource:{requestId:'r',chatSessionId:'s'}},{last:null,count:0});
 res=await wrapper.execute('id3',{command:'Get-Content x.txt -Raw',background:false});t('pty-read-wrapper-two-calls',calls.length,2);t('pty-read-second-direct',calls[1].payload.execution,'direct');t('pty-read-uses-recovered-result',res.details.summary,'direct-ok');
 calls=[];wrapper=ctx.Uz(desc,{executeTool:async c=>{calls.push(c);return{result:ptyEmpty}},callSource:{requestId:'r',chatSessionId:'s'}},{last:null,count:0});
 res=await wrapper.execute('id4',{command:'Set-Content x.txt ok',background:false});t('pty-mutation-wrapper-one-call',calls.length,1);

 // 4. Common initial/manual tool preflight (covers initialExecutions before Agent continuation).
 const commonCode=range('function DPP_COMMON_DESCRIPTOR_33','function a2(');
 const readDesc={name:'read_files',invocationName:'read_files',descriptorId:'mcp:shun:read_files',inputSchema:{type:'object',required:['paths'],properties:{paths:{type:'array'}}}};
 const common=load(effectCode+izCode+uzCode+commonCode,['DPP_COMMON_DESCRIPTOR_33','DPP_COMMON_PREFLIGHT_33'],{
   DPP_TOOL_BASE_31:e=>String(e??'').toLowerCase().split(/[.:/]/).pop(),
   DPP_CAPABILITY_WINDOW_32:()=>null,DPP_MODEL_RESULT_BUDGET_3:()=>9000,zz:e=>e,Rz:e=>e,
   DPP_STABLE_3:e=>JSON.stringify(e),iX:[desc,readDesc]
 });
 let pre=common.DPP_COMMON_PREFLIGHT_33({name:'read_files',invocationName:'read_files',descriptorId:'mcp:shun:read_files',payload:{}});
 t('common-read-empty-block',pre?.error?.code,'dpp_tool_arguments_missing');
 t('common-read-required-name',pre?.detail?.includes('paths'),true);
 pre=common.DPP_COMMON_PREFLIGHT_33({name:'run_command',invocationName:'run_command',payload:{}});
 t('common-run-empty-block',pre?.error?.code,'dpp_tool_arguments_missing');
 pre=common.DPP_COMMON_PREFLIGHT_33({name:'run_command',invocationName:'run_command',payload:{command:dangerous,background:false}});
 t('common-dangerous-encoding-block',pre?.error?.code,'dpp_windows_text_encoding_unsafe');
 pre=common.DPP_COMMON_PREFLIGHT_33({name:'run_command',invocationName:'run_command',payload:{command:'Get-Content $r -Raw -Encoding UTF8',background:false}});
 t('common-safe-run-pass',pre,null);

 // 5. Static production hooks.
 t('prompt-utf8-rule',source.includes('[Fix 3.3 UTF-8 safety]'),true);
 t('prompt-workspace-rule',source.includes('[Fix 3.3 workspace]'),true);
 t('stream-error-has-markers',source.includes('Last stream markers:'),true);
 t('stream-finish-helper-hook',source.includes('function UI(e,t){return DPP_STREAM_TERMINAL_331(e,t)}'),true);
 t('safe-eof-retry-hook',source.includes('s=!o.finished&&!i&&o.responseMessageId==null&&o.requestMessageId==null&&n<zR'),true);
 t('common-preflight-hook',source.includes('let d=DPP_COMMON_PREFLIGHT_33(e);if(d)return d;'),true);

 if(fail){console.error(`FIX33_KNOWN_ISSUES_FAIL pass=${pass} fail=${fail}`);process.exit(1)}
 console.log(`FIX33_KNOWN_ISSUES_PASS ${pass}`);
})().catch(e=>{console.error(e);process.exit(1)});
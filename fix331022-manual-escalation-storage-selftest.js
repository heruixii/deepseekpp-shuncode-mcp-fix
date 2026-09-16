const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const main=fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8');
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;
function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
(async()=>{
test('version',['1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31'].includes(manifest.version_name));

// Manual completion -> zero-tool Agent escalation is gated on a *finished* turn.
test('manual escalation marker present',content.includes('DPP_MANUAL_TOOL_INTENT_PROMPT_331022'));
test('finished state retained by response parser',content.includes('streamFinished:n.dppStreamFinished331015===!0?!0:n.dppStreamFinished331015===!1?!1:null'));
test('manual escalation requires zero tools, no resume, finished stream, and text-or-reasoning intent',content.includes('n.length===0&&!DPPResume&&e.streamFinished===!0&&DPP_TOOL_INTENT_331021(e.text,e.reasoningTail??``)'));
test('incomplete stream cannot bypass finished gate',!content.includes('n.length===0&&!DPPResume&&DPP_TOOL_INTENT_331021(e.text,e.reasoningTail??``)'));
test('zero-tool gate allows manual intent',content.includes('if(n.length===0&&!DPPResume&&!DPPManualToolIntent331022)return'));
test('simple-task gate allows manual intent',content.includes('if(X$(e)&&!DPPResume&&!DPPManualToolIntent331022)return'));
test('manual escalation uses existing authorization',content.includes('i=e.requestId?jJ.get(e.requestId):void 0'));
test('manual escalation starts with no synthesized tool execution',!content.includes('DPP_SYNTH_TOOL_CALL_331022')&&!content.includes('DPP_GUESS_TOOL_ARGS_331022'));
test('manual prompt forbids invented capability data',content.includes('Never invent capability handles, arguments, or results.'));
test('manual escalation diagnostic stage wired',content.includes('content_manual_tool_intent_escalation_331027'));
test('manual UI marker wired',content.includes('data-dpp-manual-tool-intent'));
test('manual reasoning signal is bounded',content.includes('reasoningTail:typeof n.dppReasoningTail331025==`string`?n.dppReasoningTail331025.slice(-4096):``'));
test('manual reasoning diagnostic stores no raw reasoning',content.includes('reasoningChars:(e.reasoningTail??``).length,reasoningIntent:DPPManualReasoningIntent331025'));
function manualEscalates({tools=0,resume=false,finished=true,intent=true}={}){return tools===0&&!resume&&finished===true&&intent}
test('model: finished no-tool explicit intent escalates',manualEscalates()===true);
test('model: incomplete explicit intent stays manual',manualEscalates({finished:false})===false);
test('model: existing tool execution does not duplicate Agent start',manualEscalates({tools:1})===false);
test('model: durable resume takes precedence',manualEscalates({resume:true})===false);
test('model: ordinary final text does not escalate',manualEscalates({intent:false})===false);

// Real recovery state machine: normal generation_err -> compact; compact generation_err -> raw passthrough.
const rs=main.indexOf('var DPP_GENERATION_ERR_RECOVERY_331020='),re=main.indexOf('function Sa(e)',rs);
if(rs<0||re<0)throw Error('recovery block missing');
const recoveryEvents=[];
const rctx={Map,Date,String,Array,Math,DPP_PREFLIGHT_331018:e=>recoveryEvents.push(e)};
vm.createContext(rctx);vm.runInContext(main.slice(rs,re),rctx);
function genErr(id){return {assistantMessageId:id,dppStreamFinished331015:false,dppControlTrail331017:[{path:'finish_reason',value:'generation_err'}]}}
const base={chatSessionId:'s1',requestId:'r1',parentMessageId:0,dppRequestDiag331015:{recoveryMode:null}};
rctx.DPP_TRACK_GENERATION_RESULT_331020(base,genErr(2));
test('normal generation_err arms compact',recoveryEvents.at(-1)?.stage==='mw_generation_err_recovery_armed');
test('matching parent consumes compact',rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s1',requestId:'r2',parentMessageId:2})==='compact');
const compactReq={chatSessionId:'s1',requestId:'r2',parentMessageId:2,dppRequestDiag331015:{recoveryMode:'compact'}};
rctx.DPP_TRACK_GENERATION_RESULT_331020(compactReq,genErr(4));
test('compact generation_err arms passthrough',recoveryEvents.at(-1)?.stage==='mw_generation_err_passthrough_armed_331026');
test('matching parent is forced raw passthrough',rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s1',requestId:'r3',parentMessageId:4})==='passthrough');
test('passthrough selection breadcrumb emitted',recoveryEvents.at(-1)?.stage==='mw_generation_err_passthrough_331026');
test('passthrough selection is one-shot until response outcome re-arms it',rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s1',requestId:'r4',parentMessageId:4})===null);
rctx.DPP_TRACK_GENERATION_RESULT_331020({...base,chatSessionId:'s2'},genErr(10));
test('wrong parent does not consume compact',rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s2',requestId:'x',parentMessageId:9})===null);
test('right parent still consumes after mismatch',rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s2',requestId:'y',parentMessageId:10})==='compact');
test('finished response clears pending recovery',(()=>{rctx.DPP_TRACK_GENERATION_RESULT_331020({...base,chatSessionId:'s3'},genErr(20));rctx.DPP_TRACK_GENERATION_RESULT_331020({...base,chatSessionId:'s3'},{dppStreamFinished331015:true});return rctx.DPP_RECOVERY_MODE_331020({chatSessionId:'s3',parentMessageId:20})===null})());

// Diagnostic batcher: 20 breadcrumbs -> one storage write, not 20 whole-array rewrites.
const ds=content.indexOf('var DPP_DIAG_BATCH_STATE_331022='),de=content.indexOf('async function DPP_RECORD_WEB_DIAG_331015',ds);
if(ds<0||de<0)throw Error('diagnostic batch helper missing');
let timers=[],sets=0,store={};
const dctx={Map,Promise,Object,Array,console,window:{addEventListener(){}},setTimeout(fn){timers.push(fn);return timers.length},clearTimeout(){},chrome:{storage:{local:{async get(k){return {[k]:store[k]}},async set(o){sets++;Object.assign(store,o)}}}}};
vm.createContext(dctx);vm.runInContext(content.slice(ds,de),dctx);
for(let i=0;i<20;i++)await dctx.DPP_DIAG_BATCH_APPEND_331022('k',96,{i});
test('diagnostics do not write per breadcrumb',sets===0);
await dctx.DPP_DIAG_BATCH_FLUSH_331022('k');
test('twenty diagnostics coalesce to one write',sets===1,`sets=${sets}`);
test('coalesced diagnostic keeps all burst records',store.k.length===20);
for(let i=20;i<40;i++)await dctx.DPP_DIAG_BATCH_APPEND_331022('k',24,{i});
await dctx.DPP_DIAG_BATCH_FLUSH_331022('k');
test('second burst adds only one more write',sets===2,`sets=${sets}`);
test('diagnostic ring honors tighter bound',store.k.length===24,`len=${store.k.length}`);
test('diagnostic writer no longer embeds per-record local.set',!content.slice(content.indexOf('function DPP_RECORD_PREFLIGHT_331018'),content.indexOf('async function _Z(e)')).includes('await chrome.storage.local.set'));

// Usage telemetry: callers return immediately; burst persistence is coalesced and barriers flush it.
const us=bg.indexOf('var DPP_USAGE_FLUSH_DELAY_331023='),ue=bg.indexOf('var fm=DPP_USAGE_BUFFER_331022(mm)',us);
if(us<0||ue<0)throw Error('usage buffer helper missing');
let utimers=[],writes=[];
const uctx={Promise,Object,console,setTimeout(fn){utimers.push(fn);return utimers.length},clearTimeout(){}};
vm.createContext(uctx);vm.runInContext(bg.slice(us,ue),uctx);
const buf=uctx.DPP_USAGE_BUFFER_331022(async batch=>{writes.push(batch.slice());return batch});
const ret=await buf.mutate({id:1});
await buf.mutate({id:2});await buf.mutate({id:3});await buf.mutate({id:4});await buf.mutate({id:5});
test('usage mutate acknowledges without storage wait',ret.id===1&&writes.length===0);
await buf.barrier(async()=>true);
test('five usage records coalesce into one persistence batch',writes.length===1&&writes[0].length===5,JSON.stringify(writes.map(x=>x.length)));
test('usage cache marker present',bg.includes('DPP_USAGE_CACHE_331022'));
test('usage read path uses cache',bg.includes('if(DPP_USAGE_CACHE_331022)return DPP_USAGE_CACHE_331022')&&bg.includes('DPP_USAGE_CACHE_331022=bm(r)'));
test('usage retention contract unchanged',bg.includes('lm=5e3,um=180'));

// Release/security invariants.
test('compact execution still uses full authorization descriptors',content.includes('toolDescriptors:r.descriptors'));
test('compact remains model-facing only',content.includes('DPP_COMPACT_DESCRIPTORS_331020(r.descriptors)'));
test('capability alias security path retained',content.includes('DPPInstallAliases331019')||content.includes('DPP_INSTALL_ALIASES_331019')||content.includes('DPPAliases331019'));
test('3.3.10.21 specialized steering retained',content.includes('DPP_TOOL_INTENT_NUDGE_MAX_331021=3'));

console.log(`FIX331022_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

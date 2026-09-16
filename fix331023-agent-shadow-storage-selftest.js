const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;
function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
(async()=>{
test('version',['1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32'].includes(manifest.version_name));
const js=content.indexOf('async function Jz(e)'); const je=content.indexOf('function Yz(e)',js);
if(js<0||je<0)throw Error('Jz block missing');
const jz=content.slice(js,je);
test('parent accessor exists',jz.includes('h=()=>p===`official-api`?null:f.parentMessageId'));
test('old shadowing declaration removed',!jz.includes('let h=DPP_STAT_CLAIM_MISMATCH_33109'));
test('stat mismatch uses unique stable identifier',jz.includes('let DPPStatMismatch331023=DPP_STAT_CLAIM_MISMATCH_33109(n,g)'));
test('unique stat mismatch value propagated',jz.includes('y.completionReason=DPPStatMismatch331023'));
test('turn decision still calls parent accessor',jz.includes('responseMessageId:h()'));
test('tool intent steering still calls parent accessor',jz.includes('stage:`tool_intent_steering`')&&jz.includes('responseMessageId:h()'));
test('terminal promotion still calls parent accessor',jz.includes('stage:`terminal_promotion`')&&jz.includes('responseMessageId:h()'));
test('agent exception breadcrumb added',jz.includes('stage:`agent_exception_331023`'));
test('agent exception breadcrumb records safe error fields',jz.includes('errorName:e instanceof Error?e.name:`Error`')&&jz.includes('errorMessage:e instanceof Error?e.message:String(e)')&&jz.includes('stackHead:e instanceof Error&&typeof e.stack==`string`?e.stack:``'));
// Guard the exact JS lexical failure mechanism that produced "h is not a function".
function oldHazard(stat){let h=()=>12; return (()=>{let q=()=>h(); let h=stat; return q()})()}
let oldFailed=false;try{oldHazard(null)}catch(e){oldFailed=/not a function/.test(String(e))}
test('regression reproducer models old shadowing failure',oldFailed);
function fixedHazard(stat){let h=()=>12; return (()=>{let q=()=>h(); let DPPStatMismatch331023=stat; return q()})()}
test('renamed stat binding preserves parent accessor call',fixedHazard(null)===12&&fixedHazard('x')===12);

const ds=content.indexOf('function DPP_RECORD_AGENT_TURN_DIAG_331021('),de=content.indexOf('async function _Z(',ds);
const diag=content.slice(ds,de);
test('agent diagnostic accepts errorName',diag.includes('errorName:typeof t.errorName==`string`'));
test('agent diagnostic bounds errorMessage',diag.includes('t.errorMessage.slice(0,300)'));
test('agent diagnostic bounds stackHead',diag.includes('t.stackHead.slice(0,1200)'));
test('diagnostic still excludes prompt bodies',!diag.includes('originalPrompt')&&!diag.includes('agentTaskPrompt'));

// Storage-pressure reductions are explicit and bounded.
test('execution block aggregate budget halved',content.includes('DPP_EXEC_BLOCK_BUDGET_336=131072'));
test('execution block single budget tightened',content.includes('DPP_EXEC_BLOCK_SINGLE_BUDGET_336=49152'));
test('agent trace aggregate budget further tightened',content.includes('function DPP_TRIM_AGENT_TRACES_333(e,t=65536)'));
test('tool history byte cap further tightened',bg.includes('return Math.min(Math.floor(e*O_),65536)'));
test('usage flush delay is fifteen seconds',bg.includes('DPP_USAGE_FLUSH_DELAY_331023=15e3'));
test('usage history retention count unchanged',bg.includes('lm=5e3,um=180'));

// Execute the real usage buffer helper with fake timers and verify the delay, not just a string marker.
const us=bg.indexOf('var DPP_USAGE_FLUSH_DELAY_331023='),ue=bg.indexOf('var fm=DPP_USAGE_BUFFER_331022(mm)',us);
if(us<0||ue<0)throw Error('usage buffer block missing');
let delays=[],writes=[];
const ctx={Promise,Object,console,setTimeout(fn,ms){delays.push(ms);return 1},clearTimeout(){}};
vm.createContext(ctx);vm.runInContext(bg.slice(us,ue),ctx);
const buf=ctx.DPP_USAGE_BUFFER_331022(async batch=>{writes.push(batch);return batch});
await buf.mutate({id:1}); await buf.mutate({id:2});
test('usage burst schedules one timer',delays.length===1,JSON.stringify(delays));
test('usage timer uses 15s delay',delays[0]===15000,String(delays[0]));
test('usage mutation does not eagerly write',writes.length===0);
await buf.barrier(async()=>true);
test('barrier flushes pending usage as one batch',writes.length===1&&writes[0].length===2);

// Security/recovery features from .19-.22 remain present.
test('capability alias still routes through mcp_invoke',content.includes('DPPInvokeTool331019.execute'));
test('manual tool intent escalation retained',content.includes('DPP_MANUAL_TOOL_INTENT_PROMPT_331022'));
test('compact failure breaker superseded by passthrough recovery',fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8').includes('mw_generation_err_passthrough_armed_331026'));
test('no synthetic tool guessing introduced',!content.includes('DPP_SYNTH_TOOL_CALL_331023')&&!content.includes('DPP_GUESS_TOOL_ARGS_331023'));
console.log(`FIX331023_PASS ${pass}/${total}`); if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

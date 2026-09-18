const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function between(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw Error(`missing ${a}`);return s.slice(i,j)}
(async()=>{
test('version',['1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.53'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.48'].includes(manifest.version_name));
test('direct continuation helper marker',content.includes('function DPP_DIRECT_CONTINUE_CUE_331027'));
test('manual escalation marker bumped',content.includes('content_manual_tool_intent_escalation_331027'));
test('manual diagnostic logs boolean only',content.includes('visibleContinuation:DPPManualVisibleContinuation331027'));
test('capability readiness helper marker',content.includes('function DPP_CAPABILITY_READY_331028'));
test('steering exposes boolean readiness',content.includes('`<capability_ready>`,ready?`true`:`false`'));
test('steering still forbids invented handles',content.includes('Never invent a capability handle, tool arguments, or execution result'));

const cueBlock=between(content,'function DPP_DIRECT_CONTINUE_CUE_331027','var DPP_TOOL_INTENT_NUDGE_MAX_331021=');
const ctx={String};vm.createContext(ctx);vm.runInContext(cueBlock+';globalThis.direct=DPP_DIRECT_CONTINUE_CUE_331027;globalThis.mid=DPP_MIDSTEP_CUE_31;',ctx);
const positives=[
 '页面内容已成功加载。继续读取剩余内容。',
 '接着查看后续行。',
 '下面我继续分析剩余部分。',
 '我来读取后面的内容。',
 'Continue reading the remaining content.',
 'I will continue checking the next section.'
];
for(const x of positives)test('continuation positive: '+x,ctx.mid(x)===true);
const negatives=[
 '页面内容已经全部读取完成，下面是最终总结。',
 '你可以继续阅读文档的后半部分。',
 'The task is complete. You can continue reading if you want.',
 '我已经完成检查，结果如下。'
];
for(const x of negatives)test('continuation negative: '+x,ctx.mid(x)===false);

// Evaluate production DPP_TOOL_INTENT with controlled dependencies, proving visible-midstep reasoning fallback.
const toolFn=content.match(/function DPP_TOOL_INTENT_331021\(e,t\)\{[^}]+\}/)?.[0];
if(!toolFn)throw Error('tool intent function missing');
const tctx={String,
 DPP_TOOL_INTENT_TEXT_331021:x=>/run_command|mcp_invoke|call tool/i.test(String(x||'')),
 DPP_UNCONSUMED_TOOL_MARKUP_331024:()=>false,
 Sz:x=>String(x).includes('<task_complete>')?{}:null,
 DPP_MIDSTEP_CUE_31:x=>ctx.mid(x),DPP_STRICT_CONTINUATION_31:()=>false,
 Mz:()=>false,jz:x=>String(x)
};vm.createContext(tctx);vm.runInContext(toolFn+';globalThis.ti=DPP_TOOL_INTENT_331021;',tctx);
test('visible midstep may use reasoning tool intent',tctx.ti('页面内容已加载。继续读取剩余内容。','I need to call mcp_invoke with run_command')===true);
test('visible concrete final suppresses stale reasoning',tctx.ti('页面内容已经全部读取完成，下面是最终总结。','I need to call mcp_invoke with run_command')===false);
test('empty visible text falls back to reasoning',tctx.ti('','I need to call mcp_invoke with run_command')===true);
test('task_complete suppresses reasoning',tctx.ti('<task_complete>{"summary":"done"}</task_complete>','I need to call mcp_invoke')===false);

const capFn=content.match(/function DPP_CAPABILITY_READY_331028\(e\)\{[\s\S]*?\}function DPP_TOOL_INTENT_STEERING_331021/)?.[0]?.replace(/function DPP_TOOL_INTENT_STEERING_331021[\s\S]*$/,'');
if(!capFn)throw Error('capability helper missing');
const cctx={Array,String};vm.createContext(cctx);vm.runInContext(capFn+';globalThis.ready=DPP_CAPABILITY_READY_331028;',cctx);
test('successful discover makes capability ready',cctx.ready([{name:'mcp_discover',result:{ok:true,output:{candidates:[{capability:'mcp_cap_real'}]}}}])===true);
test('successful describe makes capability ready',cctx.ready([{name:'mcp_describe',result:{ok:true,output:{capability:'mcp_cap_real',inputSchema:{type:'object'}}}}])===true);
test('failed/replayed result not capability ready',cctx.ready([{name:'mcp_invoke',result:{ok:false,error:{code:'mcp_capability_handle_replayed'}}}])===false);
test('empty execution list not capability ready',cctx.ready([])===false);

// Safe final must still consult Az; exact live final text now yields continuation via Az->midstep.
const azMatch=content.match(/function Az\(e,t,n\)\{[^}]+\}/)?.[0];
if(!azMatch)throw Error('Az missing');
const azctx={Sz:()=>null,DPP_UNCONSUMED_TOOL_MARKUP_331024:()=>false,jz:x=>x,Mz:()=>false,DPP_MIDSTEP_CUE_31:x=>ctx.mid(x),DPP_STRICT_CONTINUATION_31:()=>false};vm.createContext(azctx);vm.runInContext(azMatch+';globalThis.az=Az;',azctx);
test('live false-final is continuation',azctx.az('继续',[], '页面内容已成功加载。继续读取剩余内容。')===true);
test('real final remains final',azctx.az('继续',[], '页面内容已经全部读取完成，下面是最终总结。')===false);

// No unsafe auto synthesis added.
const region=between(content,'function DPP_CAPABILITY_READY_331028','function DPP_TOOL_INTENT_LIMIT_331021');
test('capability-aware steering does not call tools itself',!region.includes('executeTool(')&&!region.includes('mcp_cap_')&&!region.includes('toolExecutions.push'));
test('manual prompt does not include raw reasoning',!between(content,'function DPP_MANUAL_TOOL_INTENT_PROMPT_331022','async function J$(').includes('reasoningTail'));
console.log(`FIX331027_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

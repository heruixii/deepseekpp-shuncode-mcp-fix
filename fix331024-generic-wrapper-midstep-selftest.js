const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;
function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function extract(a,b){const i=content.indexOf(a),j=content.indexOf(b,i);if(i<0||j<0)throw Error(`extract ${a}`);return content.slice(i,j)}
(async()=>{
test('version',['1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.40'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.35'].includes(manifest.version_name));
// Evaluate the exact new generic-wrapper helper with minimal catalog stubs.
const helper=extract('var DPP_GENERIC_TOOL_OPEN_331024=','function Da(');
const calls=[];
const catalog={
 descriptorByInvocationName:new Map([['mcp_invoke',{name:'mcp_invoke',invocationName:'mcp_invoke'}]]),
 descriptorByName:new Map([['mcp_invoke',{name:'mcp_invoke',invocationName:'mcp_invoke'}]])
};
const ctx={String,Object,Array,JSON,Map,
 ct:x=>x&&x.__catalog?x.__catalog:catalog,
 Fa:x=>!!x&&typeof x==='object'&&!Array.isArray(x),
 DPP_CAP_ALIAS_HANDLE_331019:x=>typeof x==='string'&&/^mcp_cap_[A-Za-z0-9-]{16,}$/.test(x),
 lt:(name,payload,raw,cat)=>({name,invocationName:name,payload,raw,catalog:cat})
};
vm.createContext(ctx);vm.runInContext(helper+';globalThis.parse=DPP_PARSE_GENERIC_TOOL_WRAPPER_331024;globalThis.hasMarkup=DPP_UNCONSUMED_TOOL_MARKUP_331024;',ctx);
const cap='mcp_cap_0159d747-6be4-47f2-8c7a-b5576ee7ac1e';
const command='cd "/d/learn/Athena计划/ds_share" || exit 1\npython3 - <<\'PY\'\nprint("ok")\nPY';
const valid=`<tool_invoke>\n${JSON.stringify({capability:cap,arguments:{command}})}\n</tool_invoke>`;
let r=ctx.parse(valid,[]);
test('real wrapper sample is seen',r.seen===1);
test('real wrapper sample normalizes once',r.calls.length===1&&r.rejected===0);
test('normalized target is mcp_invoke',r.calls[0].invocationName==='mcp_invoke');
test('capability preserved exactly',r.calls[0].payload.capability===cap);
test('arguments preserved exactly',r.calls[0].payload.arguments.command===command);
test('raw wrapper retained only inside call metadata',r.calls[0].raw===valid);

r=ctx.parse(`<tool_invoke>${JSON.stringify({capability:'bad',arguments:{command:'echo x'}})}</tool_invoke>`,[]);
test('invalid capability rejected',r.calls.length===0&&r.rejected===1);
r=ctx.parse(`<tool_invoke>${JSON.stringify({capability:cap,arguments:'echo x'})}</tool_invoke>`,[]);
test('non-object arguments rejected',r.calls.length===0&&r.rejected===1);
r=ctx.parse(`<tool_invoke>${JSON.stringify({capability:cap,arguments:{command:'echo x'},extra:true})}</tool_invoke>`,[]);
test('extra top-level field rejected',r.calls.length===0&&r.rejected===1);
r=ctx.parse(`<tool_invoke>{not json}</tool_invoke>`,[]);
test('malformed json rejected',r.calls.length===0&&r.rejected===1);
r=ctx.parse(`<tool_invoke>${JSON.stringify({capability:cap,arguments:{command:'echo x'}})}`,[]);
test('unterminated wrapper rejected',r.calls.length===0&&r.rejected===1&&r.seen===1);
const noMcp={__catalog:{descriptorByInvocationName:new Map(),descriptorByName:new Map()}};
r=ctx.parse(valid,noMcp);
test('no mcp_invoke descriptor means no normalization',r.calls.length===0&&r.rejected===1);
r=ctx.parse(`<tool_call>${JSON.stringify({capability:cap,arguments:{command:'echo x'}})}</tool_call>`,[]);
test('tool_call is not normalized into execution',r.calls.length===0&&r.seen===0);
test('tool_invoke residual markup detector',ctx.hasMarkup(valid)===true);
test('tool_call residual markup detector',ctx.hasMarkup('<tool_call>{}</tool_call>')===true);
test('normal answer has no residual markup',ctx.hasMarkup('任务完成。')===false);

// Exact mid-step classifier from production source.
const mid=extract('function DPP_DIRECT_CONTINUE_CUE_331027(','var DPP_TOOL_INTENT_NUDGE_MAX_331021');
const c2={String};vm.createContext(c2);vm.runInContext(mid+';globalThis.mid=DPP_MIDSTEP_CUE_31;',c2);
test('real false-final Chinese sentence is mid-step',c2.mid('curl 只拿到了 SPA 外壳（内容由前端异步加载，HTML 里没有对话正文）。我试试分享链接背后的数据接口。')===true);
test('Chinese let-me-try API is mid-step',c2.mid('让我试试这个 API 接口。')===true);
test('English let me try endpoint is mid-step',c2.mid('Let me try the API endpoint.')===true);
test('English I will try curl is mid-step',c2.mid('I will try curl on the URL.')===true);
test('concrete completed answer is not mid-step',c2.mid('验证已通过，文件存在且 UTF-8 解码正常。')===false);

// Production wiring / defense in depth.
test('stream suppressor hides tool_invoke',content.includes('key:`generic:tool_invoke`,openTag:DPP_GENERIC_TOOL_OPEN_331024'));
test('stream suppressor hides tool_call',content.includes('key:`generic:tool_call`,openTag:DPP_GENERIC_TOOL_CALL_OPEN_331024'));
test('web fallback calls generic parser',content.includes('DPPGeneric331024=DPP_PARSE_GENERIC_TOOL_WRAPPER_331024(x,a)'));
test('normalized wrapper emitted only as fallback tool call',content.includes('`fallback-generic-331024`'));
test('generic wrapper diagnostic stage wired',content.includes('stage:`generic_tool_wrapper_331024`'));
test('generic wrapper diagnostic stores counts only',content.includes('wrapperNormalized:DPP_NUM_331018')&&content.includes('wrapperRejected:DPP_NUM_331018'));
test('safe final rejects unconsumed markup',content.includes('DPP_UNCONSUMED_TOOL_MARKUP_331024(i)||DPP_TOOL_INTENT_331021'));
test('continuation gate rejects unconsumed markup',content.includes('if(DPP_UNCONSUMED_TOOL_MARKUP_331024(n))return!0'));
test('tool intent treats unconsumed wrapper as intent',content.includes('DPP_UNCONSUMED_TOOL_MARKUP_331024(n)||DPP_TOOL_INTENT_TEXT_331021'));
test('prompt explicitly marks tool_invoke invalid',content.includes('<tool_call>...</tool_call>, <tool_invoke>...</tool_invoke>'));
test('agent rule explicitly forbids generic wrapper',content.includes('[Fix 3.3.10.24 tool wrapper] Never emit <tool_invoke> or <tool_call>'));
test('normalization requires exact two top-level keys',content.includes('p.length!==2||p[0]!==`arguments`||p[1]!==`capability`'));
test('normalization requires capability handle',content.includes('!DPP_CAP_ALIAS_HANDLE_331019(f.capability)'));
test('normalization requires plain arguments object',content.includes('!Fa(f.arguments)'));
test('normalization does not dispatch run_command directly',!helper.includes('run_command')&&!helper.includes('executeTool'));
test('existing capability security path retained',content.includes('DPPInvokeTool331019.execute'));
test('capability window warns schema is absent',content.includes('Candidate summaries do not include an argument schema'));
test('agent rule requires describe before guessing args',content.includes('call mcp_describe before mcp_invoke and do not guess optional fields'));
test('old h-shadow stays absent',!content.includes('let h=DPP_STAT_CLAIM_MISMATCH_33109'));
test('agent exception breadcrumb retained',content.includes('agent_exception_331023'));
console.log(`FIX331024_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

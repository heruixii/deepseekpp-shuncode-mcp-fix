const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;
function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}

test('version',['1.14.0.26','1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.39'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.21','1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.34'].includes(manifest.version_name));

const hs=content.indexOf('var DPP_TOOL_INTENT_NUDGE_MAX_331021='),he=content.indexOf('function DPP_NUDGE_LIMIT_31(',hs);
if(hs<0||he<0)throw Error('331021 helper block missing');
const ctx={
  String,Array,Object,JSON,RegExp,Number,Math,
  he:'zh-CN',
  jz:e=>{e=String(e??'').trim();return e.length>600?e.slice(-600):e},
  Mz:e=>/(?:let me|让我|接下来|下一步|then|now|需要|准备|打算|将要|要)[\s\S]{0,120}(?:run|call|invoke|fetch|curl|command|tool|执行|运行|调用|访问|抓取|搜索|读取)/i.test(String(e??'')),
  DPP_MIDSTEP_CUE_31:e=>/(?:let me|让我|接下来|下一步|then|now|需要|准备|打算|将要|要)[\s\S]{0,160}(?:run|call|invoke|fetch|curl|command|tool|执行|运行|调用|访问|抓取|搜索|读取)/i.test(String(e??'')),
  DPP_STRICT_CONTINUATION_31:e=>false,
  Sz:e=>String(e??'').includes('<task_complete>')?{summary:'done'}:null,
  C:()=>'',DPP_AGENT_RULES_33:'',zz:(e,n)=>String(e??'').slice(0,n),Fz:e=>e,
  DPP_COMPLETION_GATE_31:()=>({ok:true}),
  Az:(orig,tools,text)=>/(?:let me|让我|接下来|下一步|then|now|需要|准备|打算|将要|要)[\s\S]{0,160}(?:run|call|invoke|fetch|curl|command|tool|执行|运行|调用|访问|抓取|搜索|读取)/i.test(String(text??'')),
  Gz:e=>String(e??''),
  DPP_UNCONSUMED_TOOL_MARKUP_331024:e=>/<\/?(?:tool_invoke|tool_call)\b/i.test(String(e??''))
};
vm.createContext(ctx);vm.runInContext(content.slice(hs,he),ctx);

test('specialized retry cap is three',ctx.DPP_TOOL_INTENT_NUDGE_MAX_331021===3);

const real1=`The capability for run_command is mcp_cap_fa76a088-a3b3-48f0-9e0c-36c5f5475291, single-use. Let me use curl to fetch the URL. Let me try fetching with curl.`;
const real2=`The curl fetched the page but it's a JS SPA. I need a fresh capability. I should call run_command again. Need fresh capability.`;
const real3=`让我用run_command执行几个curl命令来尝试。常见的参数可能是 code、share_id 或 id。让我运行命令。`;
test('real trace 1 tool intent recognized',ctx.DPP_TOOL_INTENT_331021(real1,'')===true);
test('real trace 2 tool intent recognized',ctx.DPP_TOOL_INTENT_331021(real2,'')===true);
test('real trace 3 tool intent recognized',ctx.DPP_TOOL_INTENT_331021(real3,'')===true);
test('reasoning-only tool intent recognized',ctx.DPP_TOOL_INTENT_331021('',real1)===true);
test('task_complete never tool-intent',ctx.DPP_TOOL_INTENT_331021('<task_complete>{"summary":"done"}</task_complete>',real1)===false);
test('ordinary final answer not tool intent',ctx.DPP_TOOL_INTENT_331021('已经完成修复，全部测试通过。','')===false);
test('factual mention of curl not automatically intent',ctx.DPP_TOOL_INTENT_331021('curl 是一个命令行 HTTP 客户端。','')===false);

function mode(overrides={}){return ctx.DPP_STEERING_MODE_331021({turnIndex:1,nudgeCount:0,maxNudges:8,hasToolCall:false,hasParent:true,toolIntent:true,toolIntentNudgesInStep:0,genericNudgesInStep:0,needsContinuation:true,...overrides})}
test('first explicit tool intent gets specialized steering',mode()==='tool_intent');
test('second explicit tool intent still gets specialized steering',mode({toolIntentNudgesInStep:1,genericNudgesInStep:3})==='tool_intent');
test('third explicit tool intent still gets specialized steering',mode({toolIntentNudgesInStep:2,genericNudgesInStep:3})==='tool_intent');
test('fourth explicit tool intent is blocked',mode({toolIntentNudgesInStep:3})==='none');
test('actual tool call blocks steering',mode({hasToolCall:true})==='none');
test('missing parent blocks steering',mode({hasParent:false})==='none');
test('first turn does not synthesize steering',mode({turnIndex:0})==='none');
test('global nudge cap remains enforced',mode({nudgeCount:8})==='none');
test('generic continuation first retry allowed',mode({toolIntent:false,needsContinuation:true,genericNudgesInStep:0})==='generic');
test('generic continuation second retry allowed',mode({toolIntent:false,needsContinuation:true,genericNudgesInStep:1})==='generic');
test('generic continuation third retry allowed',mode({toolIntent:false,needsContinuation:true,genericNudgesInStep:2})==='generic');
test('generic continuation fourth retry blocked',mode({toolIntent:false,needsContinuation:true,genericNudgesInStep:3})==='none');

const steering=ctx.DPP_TOOL_INTENT_STEERING_331021('读取分享链接',real3,[],2,'zh-CN');
test('steering explicitly forbids plan narration',steering.includes('不要继续叙述')||steering.includes('Do not narrate another plan'));
test('steering requires real tool call',steering.includes('真实')&&steering.includes('tool call'));
test('steering forbids invented capability/args/results',steering.includes('不得猜造')||steering.includes('Never invent'));
test('steering says rediscover stale capability',steering.includes('mcp_discover'));
test('steering carries bounded retry count',steering.includes('<tool_intent_retry>')&&steering.includes('2\n/\n3'));

const tools=[];
test('safe final promotes ordinary concrete final',ctx.DPP_SAFE_FINAL_CANDIDATE_331021('task',tools,'修复已经完成，验证 41/41 通过。','')!==null);
test('safe final rejects narrated next tool action',ctx.DPP_SAFE_FINAL_CANDIDATE_331021('task',tools,real3,'')===null);
test('safe final rejects reasoning-only intended tool action',ctx.DPP_SAFE_FINAL_CANDIDATE_331021('task',tools,'',real1)===null);
test('safe final accepts task_complete when gate passes',ctx.DPP_SAFE_FINAL_CANDIDATE_331021('task',tools,'<task_complete>{"summary":"done"}</task_complete>','')!==null);

// Live wiring / safety invariants.
test('tool success resets both retry streaks',content.includes('y.genericNudgesInStep=0,y.toolIntentNudgesInStep=0,y.lastToolIntent=!1'));
test('tool-intent path does not set generic nudge lock',!content.includes('r===`tool_intent`?(y.nudgedInStep=!0'));
test('tool-intent limit is fail closed',content.includes('DPP_TOOL_INTENT_LIMIT_331021')&&content.includes('q(`tool_intent_limit`,!0)'));
test('no tool arguments are guessed or synthesized',!content.includes('DPP_GUESS_TOOL_ARGS_331021')&&!content.includes('DPP_SYNTH_TOOL_CALL_331021'));
test('missing response chain remains fail closed',content.includes('DPP_TOOL_INTENT_CHAIN_LOST_331021'));
test('terminal promotion uses strict candidate helper',content.includes('DPP_SAFE_FINAL_CANDIDATE_331021(t.originalPrompt,g,S,te)'));

// Provider + durable diagnostic observability.
test('provider emits terminal metadata callback',content.includes('onAgentStreamTerminal')&&content.includes('responseMessageIdCandidates'));
test('turn decision diagnostic wired',content.includes('stage:`turn_decision`'));
test('tool-intent steering diagnostic wired',content.includes('stage:`tool_intent_steering`'));
test('terminal promotion diagnostic wired',content.includes('stage:`terminal_promotion`'));
test('diagnostic ring remains bounded',content.includes('DPP_DIAG_BATCH_APPEND_331022(DPP_AGENT_TURN_DIAG_KEY_331021,80,n)'));
const ds=content.indexOf('function DPP_RECORD_AGENT_TURN_DIAG_331021('),de=content.indexOf('async function _Z(',ds);
if(ds<0||de<0)throw Error('331021 diagnostic recorder missing');
const diag=content.slice(ds,de);
test('diagnostic records lengths not text bodies',diag.includes('textChars:')&&diag.includes('reasoningChars:')&&!diag.includes('fullText')&&!diag.includes('assistantText'));
test('diagnostic stores no prompt or tool argument values',!diag.includes('originalPrompt')&&!diag.includes('payload')&&!diag.includes('args:')&&!diag.includes('arguments:'));
test('diagnostic stores only bounded ids/reasons/metadata',diag.includes('responseMessageId:')&&diag.includes('requestMessageId:')&&diag.includes('decision:')&&diag.includes('finished:'));

console.log(`FIX331021_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);

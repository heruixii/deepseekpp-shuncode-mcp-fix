const fs=require('fs'),path=require('path');
const root=__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const background=fs.readFileSync(path.join(root,'background.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;
function test(n,c){total++;if(c){pass++;console.log('PASS',n)}else{console.error('FAIL',n);process.exitCode=1}}

test('version',['1.14.0.24','1.14.0.25','1.14.0.26','1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.19','1.14.0 ShunCode MCP Fix 3.3.10.20','1.14.0 ShunCode MCP Fix 3.3.10.21','1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32'].includes(manifest.version_name));

test('alias safe-name guard',content.includes('function DPP_CAP_ALIAS_NAME_331019')&&content.includes('/^[A-Za-z_][A-Za-z0-9_.:-]*$/'));
test('alias handle guard',content.includes('function DPP_CAP_ALIAS_HANDLE_331019')&&content.includes('^mcp_cap_'));
test('alias only from discover window',content.includes('DPPInstallAliases331019=e=>{let t=DPP_CAPABILITY_WINDOW_32(e)'));
test('alias requires mcp_invoke',content.includes('DPPInvokeDescriptor331019=c.find')&&content.includes('DPPInvokeTool331019'));
test('alias delegates through mcp_invoke tool',content.includes('DPPInvokeTool331019.execute(`${e}:dpp331019`,{capability:o,arguments:a},r,i)'));
test('alias never directly dispatches target name',!content.includes('executeTool331019')&&!content.includes('r({name:t,invocationName:t,payload:a}'));
test('alias rejects base-name collision',content.includes('DPPBaseToolNames331019.has(t)'));
test('alias rejects ambiguous duplicate names',content.includes('n.get(t)!==1'));
test('alias requires finite unexpired lease',content.includes('!Number.isFinite(a?.expiresAt)||a.expiresAt<=r+1e3'));
test('alias parser cache invalidated',content.includes('st.delete(c)'));
test('alias removed after invocation',content.includes('finally{DPPRemoveAlias331019(t,o)}'));
test('latest discovery replaces prior aliases',content.includes('for(let e of[...DPPAliases331019.keys()])DPPRemoveAlias331019(e)'));
test('last initial discovery seeds aliases',content.includes('DPPInitialAliasCount331019=g.length?DPPInstallAliases331019(g[g.length-1]):0'));
test('background single-use lease preserved',background.includes('mcp_cap_')&&background.includes('handle_replayed')&&background.includes('consume:!0'));

const prep=content.indexOf('DPP_AGENT_RESUME_PREPARE_331012(e,await k0())');
const zero=content.indexOf('if(n.length===0&&!DPPResume&&!DPPManualToolIntent331022)return');
test('resume prepared before zero-tool early return',prep>=0&&zero>prep);
test('zero-tool resume allowed',zero>=0);
test('ordinary skip remains fail-closed except explicit finished manual tool intent',content.includes('if(X$(e)&&!DPPResume&&!DPPManualToolIntent331022)return'));
test('resume source ids carried into agent',content.includes('resumeSourceTraceIds:DPPResume?.sourceTraceIds??[]'));
test('resume mode displayed',content.includes('data-dpp-resume-count')&&content.includes('resume:`续跑中`'));
test('resume tool facts bounded',content.includes('function DPP_RESUME_TOOL_FACTS_331019')&&content.includes('return t.slice(-12)'));
test('resume facts exclude raw output/args/payload',(()=>{const a=content.indexOf('function DPP_RESUME_TOOL_FACTS_331019'),b=content.indexOf('function DPP_RESUME_LIGHT_PROMPT_331011',a),x=content.slice(a,b);return !x.includes('.output')&&!x.includes('.args')&&!x.includes('.payload')})());
test('legacy safe-resume marker preserved',content.includes('[Fix 3.3.10.11 safe resume]'));
test('durable resume marker present',content.includes('[Fix 3.3.10.19 durable resume] This is a resume, not a new task.'));
test('resume prompt keeps verified tool results',content.includes('Verified tool results:'));
test('first step durable checkpoint',content.includes('function DPP_AGENT_CHECKPOINT_331019(e,t){return e===0'));
test('mutation durable checkpoint',content.includes('(e?.dppEffect??DPP_TOOL_EFFECT_31(e?.name))===`mutation`'));
test('legacy checkpoint cadence preserved',content.includes('function DPP_AGENT_CHECKPOINT_333(e){return(e+1)%4===0}'));

test('compact UI stylesheet',content.includes('DPP_AGENT_COMPACT_CSS_ID_331019'));
test('stream hidden by default',content.includes('.dpp-agent-container .dpp-agent-stream { display: none !important;'));
test('details opt-in',content.includes('[data-details-open="true"] .dpp-agent-stream')&&content.includes('dpp-agent-details-btn'));
test('reasoning hidden',content.includes('.dpp-agent-reasoning-note,')&&content.includes('.dpp-agent-step,')&&content.includes('display: none !important;'));
test('final answer separate',content.includes('dpp-agent-final-answer')&&content.includes('DPP_AGENT_FINAL_331019(Q,u)'));
test('budget pause not rendered as final answer',content.includes('!a&&u&&DPP_AGENT_FINAL_331019(Q,u)'));
test('provider uuid removed from live tool label',content.includes('DPP_AGENT_STATUS_TOUCH_331010(`tool`,DPP_TOOL_NAME_33('));
test('compact status has running/recovery states',content.includes('recover:`发送“继续”恢复`')&&content.includes('badge:{starting:`准备`,running:`运行中`,complete:`完成`,paused:`暂停`,error:`未完成`}'));

function install(candidates,base,now){
  const counts=new Map();
  for(const c of candidates){if(typeof c?.name==='string'&&/^[A-Za-z_][A-Za-z0-9_.:-]*$/.test(c.name))counts.set(c.name,(counts.get(c.name)||0)+1)}
  const aliases=new Map();
  for(const c of candidates){
    if(typeof c?.name!=='string'||!/^[A-Za-z_][A-Za-z0-9_.:-]*$/.test(c.name))continue;
    if(typeof c?.capability!=='string'||!/^mcp_cap_[A-Za-z0-9-]{16,}$/.test(c.capability))continue;
    if(counts.get(c.name)!==1||base.has(c.name))continue;
    if(!Number.isFinite(c.expiresAt)||c.expiresAt<=now+1000)continue;
    aliases.set(c.name,c.capability);
  }
  return aliases;
}
const now=Date.now(),base=new Set(['mcp_discover','mcp_invoke']);
const aliases=install([
  {name:'run_command',capability:'mcp_cap_1234567890abcdef',expiresAt:now+60000},
  {name:'mcp_invoke',capability:'mcp_cap_aaaaaaaaaaaaaaaa',expiresAt:now+60000},
  {name:'bad name',capability:'mcp_cap_bbbbbbbbbbbbbbbb',expiresAt:now+60000},
  {name:'read_files',capability:'mcp_cap_cccccccccccccccc',expiresAt:now+500},
  {name:'duplicate',capability:'mcp_cap_dddddddddddddddd',expiresAt:now+60000},
  {name:'duplicate',capability:'mcp_cap_eeeeeeeeeeeeeeee',expiresAt:now+60000},
  {name:'missing_expiry',capability:'mcp_cap_ffffffffffffffff'},
],base,now);
test('behavior accepts valid discovered alias',aliases.get('run_command')==='mcp_cap_1234567890abcdef');
test('behavior blocks base collision',!aliases.has('mcp_invoke'));
test('behavior blocks invalid name',!aliases.has('bad name'));
test('behavior blocks near-expiry lease',!aliases.has('read_files'));
test('behavior blocks duplicate candidate name',!aliases.has('duplicate'));
test('behavior blocks missing expiry',!aliases.has('missing_expiry'));

console.log(`FIX331019_PASS ${pass}/${total}`);
if(pass!==total)process.exit(1);

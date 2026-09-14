const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname; const src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8'); const bg=fs.readFileSync(path.join(root,'background.js'),'utf8'); const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0;function ok(x,n){if(!x){console.error('FAIL',n);process.exit(1)}pass++;console.log('PASS',n)}
function between(a,b){let i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error('missing '+a);return src.slice(i,j)}
let code=between('DPP_EXEC_BLOCK_BUDGET_336=','function fU(');
let ctx={TextEncoder,Number,JSON,console};vm.createContext(ctx);vm.runInContext('var '+code+';globalThis.trim=DPP_TRIM_EXEC_BLOCKS_336;globalThis.compact=DPP_COMPACT_EXEC_BLOCK_336;globalThis.bytes=DPP_EXEC_BLOCK_BYTES_336;',ctx);
function exec(i){return {callId:'c'+i,name:'run_command',provider:{kind:'mcp',id:'s'},descriptorId:'d',result:{ok:true,summary:'ok',detail:'中'.repeat(900)+i,output:{stdout:'中'.repeat(900)+i}}}}
function block(id,n,age=0){return {id,source:'storage',url:'https://chat.deepseek.com/a/chat/s/x',createdAt:Date.now()+age,content:'x'.repeat(300),executions:Array.from({length:n},(_,i)=>exec(i)),metadata:{toolCount:n,mcpToolCount:n,chatSessionId:'s'}}}
let huge=block('huge',410);let c=ctx.compact(huge);ok(c.executions.length<=64,'410-execution block capped at 64');ok(ctx.bytes(c)<=65536,'single block <=64KiB');ok(c.metadata.toolCount===c.executions.length,'toolCount rewritten after compaction');ok(c.metadata.mcpToolCount===c.executions.length,'mcpToolCount rewritten after compaction');
let arr=Array.from({length:20},(_,i)=>block('b'+i,40,i));let t=ctx.trim(arr);ok(ctx.bytes(t)<=262144,'whole execution-block store <=256KiB');ok(t[t.length-1].id==='b19','newest execution block retained');
ok(src.includes('async read(){return wi(async()=>{let e=await t.readAlreadyLocked(),n=DPP_TRIM_EXEC_BLOCKS_336(e)'),'legacy oversized blocks migrate on read');
// Fake DOM nodes for mutation filter.
class E{constructor(kind,parent=null){this.kind=kind;this.parentElement=parent}closest(sel){let p=this;while(p){if(sel==='.dpp-agent-container'&&p.kind==='agent')return p;p=p.parentElement}return null}matches(sel){return sel==='.dpp-agent-container'&&this.kind==='agent'}querySelector(sel){return null}}
ctx.Element=E; vm.runInContext(between('function DPP_AGENT_OWN_NODE_336','function Q$('),ctx); let ign=ctx.DPP_AGENT_OBSERVER_IGNORABLE_336;
let agent=new E('agent'),inside=new E('inside',agent),official=new E('official');
ok(ign([{target:inside,addedNodes:[],removedNodes:[]}])===true,'observer ignores mutation inside agent subtree');
ok(ign([{target:official,addedNodes:[agent],removedNodes:[]}])===true,'observer ignores its own agent insertion');
ok(ign([{target:official,addedNodes:[],removedNodes:[agent]}])===false,'observer reacts when React removes agent container');
ok(ign([{target:official,addedNodes:[new E('react')],removedNodes:[]}])===false,'observer reacts to official-page child changes');
ok(src.includes('r=requestAnimationFrame(()=>{r=null,RY===i&&n()}'),'observer maintenance coalesced to RAF');
ok(src.includes('DPP_REASONING_RAF_336=requestAnimationFrame'),'reasoning streaming coalesced to RAF');ok(src.includes('DPP_FLUSH_REASONING_336()'),'reasoning flush wired');
ok(bg.includes('DPP_TRIM_TOOL_HISTORY_ON_START_336().catch'),'background history migration runs at startup');ok(bg.includes('new Blob([JSON.stringify(e)]).size>t'),'history migration checks byte budget');
ok(['1.14.0.1','1.14.0.2','1.14.0.3','1.14.0.4','1.14.0.5','1.14.0.6','1.14.0.7','1.14.0.8','1.14.0.9'].includes(manifest.version),'real MV3 version bumped');ok(['1.14.0 ShunCode MCP Fix 3.3.6','1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4'].includes(manifest.version_name),'version_name updated');
ok(src.includes('DPP_FRESH_POW_RETRY_335'),'Fix 3.3.5 fresh-PoW recovery preserved');ok(src.includes('DPP_MANUAL_TOOL_LIMIT_334'),'Fix 3.3.4 storm guard preserved');ok(src.includes('DPP_SAFE_DOM_332'),'Safe DOM preserved');
console.log(`FIX336_LONG_TASK_STABILITY_PASS ${pass}/${pass}`);
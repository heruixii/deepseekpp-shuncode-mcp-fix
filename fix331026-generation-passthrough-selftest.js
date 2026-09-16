const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const main=fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8');
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function between(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw Error(`missing ${a}`);return s.slice(i,j)}

(async()=>{
test('version',['1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.39'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.34'].includes(manifest.version_name));
test('main bridge validator accepts passthrough',main.includes('e.recoveryMode===`compact`||e.recoveryMode===`passthrough`'));
test('content bridge validator accepts passthrough',content.includes('e.recoveryMode===`compact`||e.recoveryMode===`passthrough`'));
test('main bridge forwards passthrough',main.includes('o===`compact`?`compact`:o===`passthrough`?`passthrough`:null'));
test('content recognizes passthrough mode',content.includes('DPPRecoveryMode331026=e.recoveryMode===`passthrough`?`passthrough`'));
test('content pass-through breadcrumb exists',content.includes('content_generation_err_passthrough_331026'));

// Evaluate production recovery state machine exactly.
const block=between(main,'var DPP_GENERATION_ERR_RECOVERY_331020=','function Sa(e)');
let now=1000000;const events=[];
class FakeDate extends Date{static now(){return now}}
const ctx={Map,Math,String,Array,Date:FakeDate,DPP_PREFLIGHT_331018:e=>events.push(e)};
vm.createContext(ctx);vm.runInContext(block+';globalThis.mode=DPP_RECOVERY_MODE_331020;globalThis.track=DPP_TRACK_GENERATION_RESULT_331020;globalThis.recovery=DPP_GENERATION_ERR_RECOVERY_331020;globalThis.streak=DPP_GENERATION_ERR_STREAK_331026;',ctx);
const gen=(aid)=>({assistantMessageId:aid,dppStreamFinished331015:false,dppControlTrail331017:[{path:'finish_reason',value:'generation_err'}]});
const finished=(aid)=>({assistantMessageId:aid,dppStreamFinished331015:true,dppControlTrail331017:[]});
const req=(mode=null,parent=0,rid='r')=>({requestId:rid,chatSessionId:'s',parentMessageId:parent,dppRequestDiag331015:{recoveryMode:mode}});

ctx.track(req(null,0,'r1'),gen(2));
test('first full generation_err arms compact',ctx.recovery.get('s')?.mode==='compact');
test('first failure streak=1',ctx.streak.get('s')?.count===1);
test('compact consumed only by matching parent',ctx.mode({requestId:'r2',chatSessionId:'s',parentMessageId:999})===null&&ctx.recovery.get('s')?.mode==='compact');
test('matching parent gets compact',ctx.mode({requestId:'r2',chatSessionId:'s',parentMessageId:2})==='compact');
ctx.track(req('compact',2,'r2'),gen(4));
test('compact failure arms passthrough',ctx.recovery.get('s')?.mode==='passthrough');
test('failure streak survives consumed compact and becomes 2',ctx.streak.get('s')?.count===2);
test('compact failure breadcrumb',events.some(e=>e.stage==='mw_generation_err_passthrough_armed_331026'&&e.failureCount===2));
test('matching parent gets passthrough',ctx.mode({requestId:'r3',chatSessionId:'s',parentMessageId:4})==='passthrough');
test('passthrough selection breadcrumb',events.some(e=>e.stage==='mw_generation_err_passthrough_331026'&&e.recoveryMode==='passthrough'));
ctx.track(req('passthrough',4,'r3'),gen(6));
test('raw failure re-arms passthrough',ctx.recovery.get('s')?.mode==='passthrough'&&ctx.recovery.get('s')?.expectedParentMessageId===6);
test('raw failure streak becomes 3',ctx.streak.get('s')?.count===3);
test('raw failure breadcrumb',events.some(e=>e.stage==='mw_generation_err_passthrough_failed_331026'&&e.failureCount===3));
now+=59000;
test('passthrough remains live inside 60s ttl',ctx.mode({requestId:'r4',chatSessionId:'s',parentMessageId:6})==='passthrough');
ctx.track(req('passthrough',6,'r4'),finished(8));
test('finished clears streak and recovery',!ctx.streak.has('s')&&!ctx.recovery.has('s'));

// TTL/reset behavior for stale streaks.
ctx.track(req(null,0,'r5'),gen(10));
now+=121000;
ctx.track(req(null,10,'r6'),gen(12));
test('failure streak resets after stale window',ctx.streak.get('s')?.count===1);

// Content must bypass before auth creation / project augmentation.
const bz=between(content,'async function bZ(e){','function xZ(e){');
const pidx=bz.indexOf('if(DPPRecoveryMode331026===`passthrough`)');
const authidx=bz.indexOf('r=await jZ(');
const projidx=bz.indexOf('await kZ(l)');
test('passthrough branch precedes authorization',pidx>=0&&authidx>pidx);
test('passthrough branch precedes project context',pidx>=0&&projidx>pidx);
const branch=bz.slice(pidx,bz.indexOf('let s=o.route===`regenerate`',pidx));
test('passthrough branch returns null augmentation only',branch.includes('xZ(t);return')&&!branch.includes('jZ(')&&!branch.includes('kZ(')&&!branch.includes('Zc('));
test('passthrough branch does not synthesize tool calls',!branch.includes('mcp_invoke')&&!branch.includes('TOOL_CALL'));
test('normal compact path still exists',content.includes('DPPRecoveryCompact331020=DPPRecoveryMode331026===`compact`'));
test('compact descriptor reduction retained',content.includes('DPP_COMPACT_DESCRIPTORS_331020(r.descriptors)'));
test('generation_err detection remains exact',block.includes('finish_reason')&&block.includes('generation_err'));
test('no automatic network replay introduced',!block.includes('fetch(')&&!block.includes('XMLHttpRequest'));

console.log(`FIX331026_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

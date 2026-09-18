require('./fix3-policy.js');
const p=globalThis.DPP_FIX3;let failed=0;
function ok(name,cond,detail=''){console.log(`${cond?'PASS':'FAIL'} ${name}${detail?' '+detail:''}`);if(!cond)failed++}
function d(name,kind='mcp',id='srv',pad=0){return{name,invocationName:name,title:name,description:'x'.repeat(pad),inputSchema:{type:'object',properties:{text:{type:'string'}}},provider:{kind,id},execution:{enabled:true,mode:'auto'}}}
const base={version:1,adaptiveMaxDirectTools:8,adaptiveMaxPromptBytes:24000,servers:{srv:{pinnedDescriptorIds:['keep-me']}}};
let small=[d('read_files','mcp','srv',100)];let a=p.promptExposureSettings(small,base,'读取文件');
ok('small-keeps-settings',a===base);
let big=Array.from({length:24},(_,i)=>d(`tool_${i}`,'mcp','srv',2400));let b=p.promptExposureSettings(big,base,'读取文件');
ok('big-clones-settings',b!==base);
ok('big-direct-to-adaptive',b.servers.srv.mode==='adaptive');
ok('pins-preserved',b.servers.srv.pinnedDescriptorIds.join(',')==='keep-me');
ok('original-not-mutated',base.servers.srv.mode===undefined);
let explicitDirect={...base,servers:{srv:{mode:'direct',pinnedDescriptorIds:[]}}};let e2=p.promptExposureSettings(big,explicitDirect,'读取文件');
ok('explicit-direct-respected-331042',e2===explicitDirect);
let shuncode=Array.from({length:15},(_,i)=>d(`sc_${i}`,'mcp','srv',1300));let s2=p.promptExposureSettings(shuncode,base,'继续');
ok('single-shuncode-server-stays-direct-331042',s2===base,String(shuncode.reduce((a,x)=>a+p.promptDescriptorCost(x),0)));
let already={...base,servers:{srv:{mode:'adaptive',pinnedDescriptorIds:[]}}};let c=p.promptExposureSettings(big,already,'读取文件');
ok('already-adaptive-identity',c===already);
let onlyLocal=Array.from({length:12},(_,i)=>d(`local_${i}`,'local','local',2400));let d2=p.promptExposureSettings(onlyLocal,base,'读取文件');
ok('local-only-no-rewrite',d2===base);
ok('obsidian-run-bonus',p.routeBonus({name:'run_command'},'读取黑曜石笔记 vault')>=850,String(p.routeBonus({name:'run_command'},'读取黑曜石笔记 vault')));
ok('generic-file-read-bonus',p.routeBonus({name:'read_files'},'读取文件')>=650);
ok('descriptor-cost-positive',p.promptDescriptorCost(d('read_files','mcp','srv',100))>1024);
const fs=require('fs'),path=require('path'),bg=fs.readFileSync(path.join(__dirname,'background.js'),'utf8');
ok('background-wired',bg.includes('globalThis.DPP_FIX3?.promptExposureSettings?.(n,r,t)??r'));
ok('single-background-wire',(bg.match(/promptExposureSettings\?\./g)||[]).length===1);
if(failed)process.exit(1);console.log('ALL_PASS 14');

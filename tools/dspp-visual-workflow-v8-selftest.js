'use strict';
// Synthetic fixtures only; no real user SVG/image/trace is included.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
const policy=fs.readFileSync(path.join(root,'fix3-policy.js'),'utf8');
function cut(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i+a.length);assert(i>=0&&j>i,a);return s.slice(i,j)}
function fn(s,name){const i=s.indexOf('function '+name+'(');assert(i>=0,name);let depth=0;for(let k=s.indexOf('{',i);k<s.length;k++){if(s[k]==='{')depth++;if(s[k]==='}'&&--depth===0)return s.slice(i,k+1)}throw Error(name)}
const helpers=cut(content,'/* DPP_VISUAL_WORKFLOW_V8_BEGIN */','/* DPP_VISUAL_WORKFLOW_V8_END */');
const scanner=cut(content,'function DPP_UNREGISTERED_TOOL_TAG_331033(','function DPP_UNREGISTERED_TAG_STEERING_331033(');
const shared={};vm.createContext(shared);vm.runInContext(helpers+scanner+';var DPP_SHUNCODE_TOOL_TAGS_331033=new Set(["apply_patch","read_image","run_command","read_files"]);',shared);
let count=0;function test(name,body){body();count++;console.log('PASS '+name)}
const prompt='参考 D:/workspace/reference.jpg 的图片，使用 HTML+CSS 精确重绘 SVG，制作可播放绘制过程的网页；禁止描摹算法 convert';
const unregistered=new Set(['mcp_discover','mcp_invoke']);
const successfulRead={name:'mcp_invoke',result:{ok:true,name:'read_image'}};
const longPatch='<apply_patch>\n*** Begin Patch\n*** Add File: demo.html\n'+('+<path d="M0 0 L10 10"/>\n'.repeat(1100))+'*** End Patch\n</apply_patch>';
function decisionBox(text,options={}){
 const decisions=[];
 const box={console,Map,Set,String,Array,Math,Date,
  Yz:e=>e.text,te:'',v:new Map,DPPAliases331019:new Map,
  t:{originalPrompt:options.prompt??prompt},g:options.results??[],p:options.backend??'web',
  y:{currentTurnIsNudge:!!options.nudge,count:options.globalLimit?8:options.nudge?3:0,toolIntentNudgesInStep:options.atLimit?3:0,genericNudgesInStep:0},
  a:'synthetic-loop',s:'synthetic-session',b:1,ue:2,h:()=>9,Ce:{maxSteps:96,maxNudges:8},
  ae:null,ie:null,oe:false,se:'',ce:'',le:false,q:null,d:'zh-CN',
  DPP_TOOL_INTENT_331021:()=>!!options.otherIntent,
  DPP_TOOL_INTENT_NUDGE_MAX_331021:3,DPP_GENERIC_NUDGE_MAX_331025:3,
  DPP_RECORD_AGENT_TURN_DIAG_331021:e=>decisions.push(e),m:()=>options.hasParent!==false,
  DPP_TOOL_INTENT_CHAIN_LOST_331021:()=> 'chain lost',
  DPP_TOOL_INTENT_LIMIT_331021:()=> 'bounded unresolved work',DPP_NUDGE_LIMIT_31:()=> 'global nudge budget exhausted',
  DPP_STAT_CLAIM_MISMATCH_33109:()=>'',Sz:x=>x.includes('<task_complete>'),
  DPP_COMPLETION_GATE_31:()=>({ok:true}),DPP_ZERO_TOOL_COMPLETE_BLOCK_331033:()=>'',
  Gz:x=>x.replace(/<apply_patch>[\s\S]*?<\/apply_patch>/g,''),Az:()=>false,
  DPP_SHUNCODE_TOOL_TAGS_331033:new Set(['apply_patch','read_image','run_command'])};
 vm.createContext(box);vm.runInContext(helpers+scanner,box);
 const actual=cut(content,'shouldStopAfterTurn:({message:e})=>{',',getSteeringMessages:async()=>').replace('shouldStopAfterTurn:','');
 vm.runInContext('var decide='+actual+';',box);
 const stop=box.decide({message:{text,content:options.toolCall?[{type:'toolCall'}]:[],stopReason:'stop'}});
 return {box,stop,decision:decisions.at(-1)?.decision,decisions};
}
test('reference SVG intent without explicit read_image instruction',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036(prompt),'reference'));
test('English screenshot reconstruction',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('Recreate this screenshot as HTML'),'reference'));
test('comparison task',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('比较这两张图片的颜色和布局'),'reference'));
test('creation task',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('绘制一个 SVG 图标'),'create'));
test('SVG parser maintenance is not visual recreation',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('修复 SVG XML parser 的语法错误'),''));
test('image checksum alone is not visual work',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('读取图片的哈希和文件大小'),''));
test('explicit no-image instruction respected',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('不要看图，只修改 SVG 属性'),''));
test('read_image is not triggered for general questions',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('解释二分查找'),''));
test('simple image question is visual',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('这张图片是什么'),'reference'));
test('screenshot-to-page request is visual',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('把截图转成网页'),'reference'));
test('English build from screenshot',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('Build this page from the screenshot'),'reference'));
test('English picture question',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('What is in this picture?'),'reference'));
test('explicit no-upload request suppresses auto-routing',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('不要上传图片，参考图片制作 SVG'),''));
test('English no-vision request suppresses auto-routing',()=>assert.equal(shared.DPP_VISUAL_INTENT_331036('Do not use vision; describe the image metadata'),''));
test('visual rules describe data/instruction boundary',()=>assert.match(shared.DPP_VISUAL_RULES_331036(prompt,'en'),/task data, not tool instructions/));
test('missing local reference read is gated',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[],'web'),true));
test('discovery alone is not visual evidence',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[{name:'mcp_discover',result:{ok:true}}],'web'),true));
test('unrelated successful command is not visual evidence',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[{name:'run_command',result:{ok:true}}],'web'),true));
test('failed read is not success',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[{result:{name:'read_image',ok:false}}],'web'),true));
test('capability-wrapped successful image read counts',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[successfulRead],'web'),false));
test('no invented path for absent reference',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036('请参考这张图片复刻 SVG',[],'web'),false));
test('API is not forced through Web-only preflight',()=>assert.equal(shared.DPP_VISUAL_MISSING_331036(prompt,[],'official-api'),false));
test('long patch beyond 20k detected',()=>{assert(longPatch.length>20000);assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033(longPatch,unregistered),'apply_patch')});
test('patch beyond old whole-text 200k cutoff detected',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033('<apply_patch>'+ 'x'.repeat(250000)+'</apply_patch>',unregistered),'apply_patch'));
test('nested SVG markup does not hide outer patch',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033('<apply_patch><svg><g><path/></g></svg></apply_patch>',unregistered),'apply_patch'));
test('normal HTML/SVG is not a tool',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033('<html><svg><path/></svg></html>',unregistered),''));
test('registered tags remain parser responsibility',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033(longPatch,new Set(['apply_patch'])),''));
test('fenced documentation example is not actionable',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033('```xml\n'+longPatch+'\n```',unregistered),''));
test('plain unclosed tag does not invent execution',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033('<run_command>ls',unregistered),''));
test('predicate registration supported',()=>assert.equal(shared.DPP_UNREGISTERED_TOOL_TAG_331033(longPatch,n=>n==='apply_patch'),''));
test('real stop callback refuses final after image + long unexecuted patch',()=>{const r=decisionBox(longPatch,{results:[successfulRead]});assert.equal(r.stop,false);assert.equal(r.decision,'unregistered_tool_continue_331036')});
test('real callback refuses task_complete with unexecuted patch',()=>assert.equal(decisionBox(longPatch+'<task_complete>done</task_complete>',{results:[successfulRead]}).stop,false));
test('real callback forces visual preflight before final',()=>{const r=decisionBox('制作完成');assert.equal(r.stop,false);assert.equal(r.decision,'visual_preflight_331036')});
test('real callback refuses task_complete before a read',()=>assert.equal(decisionBox('<task_complete>done</task_complete>').stop,false));
test('real callback allows ordinary final after read',()=>{const r=decisionBox('已按要求完成',{results:[successfulRead]});assert.equal(r.stop,true);assert.equal(r.decision,'final')});
test('real callback preserves actual tool execution',()=>{const r=decisionBox('tool',{toolCall:true});assert.equal(r.stop,false);assert.equal(r.decision,'tool_call')});
test('real callback stops bounded retries as failure, not success',()=>{const r=decisionBox(longPatch,{results:[successfulRead],nudge:true,atLimit:true});assert.equal(r.stop,true);assert.equal(r.box.oe,true);assert.equal(r.box.ie,null);assert.equal(r.decision,'unexecuted_work_limit_331036')});
test('visual missing shares bounded failure path',()=>{const r=decisionBox('计划继续',{nudge:true,atLimit:true});assert.equal(r.box.oe,true);assert.equal(r.decision,'unexecuted_work_limit_331036')});
test('no-parent unresolved work cannot become final',()=>assert.throws(()=>decisionBox(longPatch,{results:[successfulRead],hasParent:false}),/chain lost/));
test('unrelated plain final remains final',()=>assert.equal(decisionBox('二分查找的复杂度为 O(log n)',{prompt:'解释二分查找'}).decision,'final'));
test('generic tool-intent is not lost when visible-text heuristic says final',()=>assert.equal(decisionBox('继续执行工具',{prompt:'普通任务',otherIntent:true}).stop,false));
test('exhausted global budget is failure before the next local nudge',()=>{const r=decisionBox(longPatch,{results:[successfulRead],globalLimit:true});assert.equal(r.stop,true);assert.equal(r.box.oe,true);assert.match(r.box.se,/global/);assert.equal(r.decision,'unexecuted_work_limit_331036')});
test('global budget also bounds visual preflight',()=>{const r=decisionBox('准备继续',{globalLimit:true});assert.equal(r.stop,true);assert.equal(r.box.oe,true);assert.equal(r.box.ie,null)});
test('real steering consumes visualMissing state',()=>{assert(content.includes('let e=!!y.visualMissing||!!y.unregisteredTag'));assert(content.includes('y.visualMissing&&(i=`${DPP_VISUAL_RETRY_331036(d,'))});
test('real picker ranks image and writing capability for recreation',()=>{
 const box={};vm.createContext(box);vm.runInContext(policy,box);
 vm.runInContext(['DPP_CORE_TOOL_FLOOR_331033','Cd','Td','Dd','Ed'].map(n=>fn(bg,n)).join('\n'),box);
 const names=['read_files','list_directory','search_files','run_command','apply_patch','read_image','get_command_output'];
 const intent=box.Td(prompt),words=box.Dd(intent);
 const ranked=names.map(n=>({n,score:box.Cd({name:n,invocationName:'mcp_t_s_'+n,title:n,description:n},intent,words,false)})).sort((a,b)=>b.score-a.score).slice(0,5).map(x=>x.n);
 assert(ranked.includes('read_image'));assert(ranked.includes('apply_patch'));
 assert.equal(box.DPP_FIX3.routeBonus({name:'read_image',invocationName:'mcp_t_s_read_image'},'介绍 TCP 协议'),0);
});
test('real initial prompt augmentation includes visual guidance',()=>{
 const box={he:'zh-CN',Ya:()=>0,Ha:x=>x,Xa:()=>[],$a:()=>'',w:()=>'',So:()=>'',xo:()=>'',yo:()=>'',Co:()=>'',bo:()=>'',Do:()=>'',so:x=>x,co:x=>x,at:()=>[]};
 vm.createContext(box);vm.runInContext(helpers+fn(content,'vo'),box);
 assert.match(box.vo(prompt,{memoryEnabled:false,locale:'zh-CN'}).augmented,/3\.3\.10\.36 视觉工作流/);
 assert(!box.vo(prompt,{memoryEnabled:false,systemPromptEnabled:false}).augmented.includes('3.3.10.36'));
 assert(!box.vo('解释二分查找',{memoryEnabled:false}).augmented.includes('3.3.10.36'));
});
async function realSteeringTests(){
 const marker='getSteeringMessages:';let i=content.indexOf(marker)+marker.length,depth=0,end=-1;
 for(let k=content.indexOf('{',i);k<content.length;k++){if(content[k]==='{')depth++;if(content[k]==='}'&&--depth===0){end=k+1;break}}
 assert(end>i);const source=content.slice(i,end);
 for(const [name,fixture,required] of [
  ['real steering reissues discovery after long unregistered patch',decisionBox(longPatch,{results:[successfulRead]}),'mcp_discover'],
  ['real steering requests read_image after missing visual evidence',decisionBox('制作完成'),'read_image']
 ]){
  const box=fixture.box;Object.assign(box,{Cz:x=>x,DPP_TOOL_INTENT_STEERING_331021:()=> 'Use the current verified tool schema',Pz:()=> 'generic continuation'});
  vm.runInContext(fn(content,'DPP_STEERING_MODE_331021')+fn(content,'DPP_UNREGISTERED_TAG_STEERING_331033')+';var steer='+source+';',box);
  const result=await box.steer();assert.equal(result.length,1);assert(JSON.stringify(result).includes(required));assert.equal(box.y.pendingTurn,true);assert.equal(box.y.active,true);assert.equal(box.y.count,1);count++;console.log('PASS '+name);
 }
}
realSteeringTests().then(()=>console.log('RESULT '+count+'/'+count+' groups passed; offline only.')).catch(e=>{console.error(e);process.exitCode=1});

const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname;
const main=fs.readFileSync(path.join(root,'content-scripts/main-world.js'),'utf8');
const content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}

test('version',['1.14.0.25','1.14.0.26','1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.39'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.20','1.14.0 ShunCode MCP Fix 3.3.10.21','1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.34'].includes(manifest.version_name));

const hs=main.indexOf('var DPP_GENERATION_ERR_RECOVERY_331020='),he=main.indexOf('function Sa(',hs);
if(hs<0||he<0)throw Error('331020 recovery helpers missing');
let now=100000,events=[];const hctx={Map,Array,String,Math,Number,Date:{now:()=>now},DPP_PREFLIGHT_331018:e=>events.push(e)};
vm.createContext(hctx);vm.runInContext(main.slice(hs,he),hctx);
const failed=(id=2)=>({dppStreamFinished331015:false,assistantMessageId:id,dppControlTrail331017:[{path:'quasi_status',value:'INCOMPLETE'},{path:'finish_reason',value:'generation_err'}]});
const unfinished={dppStreamFinished331015:false,assistantMessageId:7,dppControlTrail331017:[{path:'response/status',value:'INCOMPLETE'}]};
const finished={dppStreamFinished331015:true,assistantMessageId:8,dppControlTrail331017:[{path:'response/status',value:'FINISHED'}]};
const meta={requestId:'auth-r1',chatSessionId:'chat-a',parentMessageId:null,originalPrompt:'SECRET-PROMPT'};

test('exact generation_err recognized',hctx.DPP_GENERATION_ERR_RESULT_331020(failed())===true);
test('ordinary incomplete not recognized',hctx.DPP_GENERATION_ERR_RESULT_331020(unfinished)===false);
hctx.DPP_TRACK_GENERATION_RESULT_331020(meta,failed(2));
test('generation_err arms one recovery',hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));
test('arm event privacy safe',events.length===1&&events[0].stage==='mw_generation_err_recovery_armed'&&events[0].requestId==='auth-r1'&&events[0].expectedParentMessageId===2&&!JSON.stringify(events[0]).includes('SECRET-PROMPT'));
test('wrong parent cannot consume recovery',hctx.DPP_RECOVERY_MODE_331020({...meta,parentMessageId:99})===null&&hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));
test('different session cannot inherit recovery',hctx.DPP_RECOVERY_MODE_331020({...meta,chatSessionId:'chat-b',parentMessageId:2})===null);
test('matching parent gets compact mode',hctx.DPP_RECOVERY_MODE_331020({...meta,parentMessageId:2})==='compact');
test('matching recovery is single-use',hctx.DPP_RECOVERY_MODE_331020({...meta,parentMessageId:2})===null&&!hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));
hctx.DPP_TRACK_GENERATION_RESULT_331020(meta,failed(4));now+=12001;
test('recovery expires after 12 seconds',hctx.DPP_RECOVERY_MODE_331020({...meta,parentMessageId:4})===null&&!hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));
now=200000;hctx.DPP_TRACK_GENERATION_RESULT_331020(meta,failed(6));hctx.DPP_TRACK_GENERATION_RESULT_331020(meta,finished);
test('finished response clears armed state',!hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));
hctx.DPP_TRACK_GENERATION_RESULT_331020(meta,{...failed(10),assistantMessageId:null});
test('missing assistant id never arms',!hctx.DPP_GENERATION_ERR_RECOVERY_331020.has('chat-a'));

const cs=content.indexOf('function DPP_COMPACT_SCHEMA_331020'),ce=content.indexOf('function Zc(',cs);
if(cs<0||ce<0)throw Error('331020 compact helpers missing');
const cctx={Array,Object,String};vm.createContext(cctx);vm.runInContext(content.slice(cs,ce),cctx);
const long='This is a deliberately long verbose explanation '.repeat(20);
const descriptor={id:'x',name:'run_command',invocationName:'run_command',title:'Run command',description:long,inputSchema:{type:'object',description:long,required:['command','background'],properties:{command:{type:'string',description:long,examples:['SECRET_EXAMPLE']},background:{type:'boolean',description:long},timeout_ms:{type:'integer',description:long,minimum:1000,maximum:120000}},additionalProperties:false,examples:[{command:'SECRET'}]}};
const compact=cctx.DPP_COMPACT_DESCRIPTORS_331020([descriptor])[0];
test('compact keeps tool identity',compact.name==='run_command'&&compact.invocationName==='run_command');
test('compact description bounded',compact.description.length<=180);
test('compact schema keeps required',JSON.stringify(compact.inputSchema.required)===JSON.stringify(['command','background']));
test('compact schema keeps types and limits',compact.inputSchema.type==='object'&&compact.inputSchema.properties.command.type==='string'&&compact.inputSchema.properties.timeout_ms.minimum===1000&&compact.inputSchema.properties.timeout_ms.maximum===120000);
test('compact schema drops verbose descriptions/examples',!JSON.stringify(compact.inputSchema).includes('SECRET')&&!JSON.stringify(compact.inputSchema).includes('deliberately long'));
const fullBytes=JSON.stringify(descriptor).length,compactBytes=JSON.stringify(compact).length;
test('compact descriptor materially smaller',compactBytes<fullBytes*0.35,`${fullBytes}->${compactBytes}`);

test('bridge accepts only null/compact recovery mode',main.includes('e.recoveryMode===void 0||e.recoveryMode===null||e.recoveryMode===`compact`')&&content.includes('e.recoveryMode===void 0||e.recoveryMode===null||e.recoveryMode===`compact`'));
test('fetch and xhr both track terminal generation result',(main.match(/DPP_TRACK_GENERATION_RESULT_331020\(/g)||[]).length>=3);
test('recovery keyed by session and expected parent',main.includes('expectedParentMessageId')&&main.includes('e?.parentMessageId!==n.expectedParentMessageId'));
test('recovery is not prompt fingerprint based',!main.includes('DPP_PROMPT_HASH_331020'));
test('preflight stores recovery metadata',content.includes('recoveryMode:t.recoveryMode===`compact`?`compact`:null')&&content.includes('expectedParentMessageId:DPP_NUM_331018'));
test('terminal web diagnostic stores compact mode',content.includes('descriptorNames:Array.isArray(t.descriptorNames)')&&content.includes('recoveryMode:t.recoveryMode===`compact`?`compact`:null'));
test('compact path skips project context',content.includes('DPPRecoveryCompact331020?null:await kZ(l)'));
test('compact path disables memory and preset cadence',content.includes('{...eX,memoryEnabled:!1,presetCadence:`off`}'));
test('compact path disables preset/project/auto skill',content.includes('activePreset:DPPRecoveryCompact331020?null:QY')&&content.includes('projectContext:DPPRecoveryCompact331020?null:')&&content.includes('skillAutoActivation:DPPRecoveryCompact331020?{everyMessage:!1,firstMessage:!1}:tX'));
test('compact path does not disable system prompt',!content.includes('DPPRecoveryCompact331020?{...eX,systemPromptEnabled:!1'));
test('authorization descriptors remain full for execution',content.includes('toolDescriptors:r.descriptors,activeLocalSkillDir:d.activeLocalSkillDir'));
test('no synthetic FINISHED added by 331020',!main.slice(hs,he).includes('FINISHED')&&!content.slice(cs,ce).includes('FINISHED'));
test('no direct replay request in recovery helper',!main.slice(hs,he).includes('fetch(')&&!main.slice(hs,he).includes('.send('));
test('parent id included in preflight',main.includes('parentMessageId:c.parentMessageId')&&main.includes('parentMessageId:i.parentMessageId'));

console.log(`FIX331020_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);

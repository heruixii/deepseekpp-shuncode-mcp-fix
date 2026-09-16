const fs=require('fs'),path=require('path'),vm=require('vm');
const root=__dirname, content=fs.readFileSync(path.join(root,'content-scripts/content.js'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c,d=''){total++;if(c){pass++;console.log('PASS',n,d)}else{console.error('FAIL',n,d);process.exitCode=1}}
function between(a,b){const i=content.indexOf(a),j=content.indexOf(b,i);if(i<0||j<0)throw Error(`missing ${a}`);return content.slice(i,j)}
(async()=>{
test('version',['1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31'].includes(manifest.version_name));
test('consumption aware helper marker',content.includes('function DPP_CAPABILITY_READY_331028'));
test('old readiness helper removed',!content.includes('function DPP_CAPABILITY_READY_331027'));
test('steering uses consumption-aware helper',content.includes('ready=DPP_CAPABILITY_READY_331028(n)'));
test('empty PTY annotation marker',content.includes('function DPP_ANNOTATE_EMPTY_PTY_331028'));
test('normalizer routes clean success through annotation',content.includes('return DPP_ANNOTATE_EMPTY_PTY_331028(e,t)'));
test('agent result annotated after direct retry decision',content.includes('f?.result&&(f.result=DPP_ANNOTATE_EMPTY_PTY_331028(e.invocationName,f.result))'));
test('result serializer keeps empty PTY hint',content.includes('e?.result?.dppEmptyPtySuccess===!0'));

const cap=between('function DPP_CAPABILITY_READY_331028','function DPP_TOOL_INTENT_STEERING_331021');
const cctx={Array,String};vm.createContext(cctx);vm.runInContext(cap+';globalThis.ready=DPP_CAPABILITY_READY_331028;',cctx);
const discover={name:'mcp_discover',result:{ok:true,output:{candidates:[{capability:'mcp_cap_real',name:'run_command'}]}}};
const describe={name:'mcp_describe',result:{ok:true,output:{capability:'mcp_cap_real',inputSchema:{type:'object'}}}};
const invokeOk={name:'mcp_invoke',result:{ok:true,summary:'done'}};
const invokeReplay={name:'mcp_invoke',result:{ok:false,error:{code:'mcp_capability_handle_replayed'}}};
const unrelated={name:'memory_save',result:{ok:true,output:{id:1}}};
test('discover alone is ready',cctx.ready([discover])===true);
test('describe alone is ready',cctx.ready([describe])===true);
test('unrelated tool after describe keeps ready',cctx.ready([describe,unrelated])===true);
test('successful invoke consumes prior capability',cctx.ready([discover,describe,invokeOk])===false);
test('failed/replay invoke also invalidates prior readiness',cctx.ready([discover,invokeReplay])===false);
test('fresh discover after invoke restores readiness',cctx.ready([discover,invokeOk,discover])===true);
test('fresh describe after invoke restores readiness',cctx.ready([discover,invokeOk,describe])===true);
test('empty execution list not ready',cctx.ready([])===false);

const ptyBlock=between('function DPP_PTY_EMPTY_33','function DPP_SHOULD_DIRECT_RETRY_33');
const pctx={String,JSON,DPP_TOOL_NAME_33:e=>String(e||'').toLowerCase().split(/[.:/]/).pop()};vm.createContext(pctx);vm.runInContext(ptyBlock+';globalThis.empty=DPP_PTY_EMPTY_33;globalThis.annotate=DPP_ANNOTATE_EMPTY_PTY_331028;',pctx);
const empty={ok:true,summary:'Run command completed',detail:'execution: pty\nstatus: completed\nexit_code: 0\ntotal_output_bytes: 0',output:null};
const annotated=pctx.annotate('run_command',empty);
test('detects empty PTY success',pctx.empty(empty)===true);
test('annotation keeps ok=true',annotated.ok===true);
test('annotation marks empty PTY success',annotated.dppEmptyPtySuccess===true);
test('annotation says invocation consumed',/single-use capability as consumed/i.test(annotated.summary));
test('annotation forbids replay',/do not replay/i.test(annotated.summary));
test('annotation prescribes fresh read-only verification',/fresh capability/i.test(annotated.summary)&&/read-only verification/i.test(annotated.summary));
const twice=pctx.annotate('run_command',annotated);
test('annotation idempotent',twice.summary===annotated.summary);
test('non-run-command unchanged',pctx.annotate('read_files',empty)===empty);
const nonempty={...empty,detail:'execution: pty\nstatus: completed\nexit_code: 0\ntotal_output_bytes: 25'};
test('nonempty PTY success unchanged',pctx.annotate('run_command',nonempty)===nonempty);
const failed={...empty,ok:false};test('failed command unchanged',pctx.annotate('run_command',failed)===failed);

const norm=between('function DPP_RUN_COMMAND_TEXT_33108','function DPP_DESCRIPTOR_PROPERTY_33108');
const nctx={String,JSON,Number,DPP_TOOL_NAME_33:pctx.DPP_TOOL_NAME_33,DPP_ANNOTATE_EMPTY_PTY_331028:pctx.annotate};vm.createContext(nctx);vm.runInContext(norm+';globalThis.norm=DPP_NORMALIZE_RUN_COMMAND_RESULT_33108;',nctx);
const normalized=nctx.norm('run_command',empty);
test('normalizer annotates exit0 empty PTY',normalized.dppEmptyPtySuccess===true);
const bad={ok:true,summary:'',detail:'execution: pty\nstatus: completed\nexit_code: 7\ntotal_output_bytes: 0'};
const badn=nctx.norm('run_command',bad);
test('normalizer still turns nonzero into failure',badn.ok===false&&badn.error?.code==='run_command_failed');

const retry=between('function DPP_SHOULD_DIRECT_RETRY_33','function DPP_MCP_TRANSIENT_VERIFICATION_33107');
test('automatic direct retry remains verification-only',retry.includes('DPP_TOOL_EFFECT_31(`run_command`,t)===`verification`'));
test('empty PTY annotator never invokes tools',!ptyBlock.includes('executeTool(')&&!ptyBlock.includes('mcp_invoke'));
test('capability helper never exposes a hardcoded handle',!cap.includes('mcp_cap_'));
test('existing no-replay contract retained',content.includes('Never replay a command merely because PTY stdout is empty.'));
console.log(`FIX331028_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

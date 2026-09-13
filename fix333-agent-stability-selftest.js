const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname;
const content=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
const bg=fs.readFileSync(path.join(root,'background.js'),'utf8');
let pass=0;
function ok(cond,msg){if(!cond){console.error('FAIL',msg);process.exit(1)} pass++;console.log('PASS',msg)}
function between(s,a,b){const i=s.indexOf(a); if(i<0)throw Error('missing '+a); const j=s.indexOf(b,i); if(j<0)throw Error('missing '+b); return s.slice(i,j)}

ok(content.includes('function DPP_AGENT_CHECKPOINT_333(e){return(e+1)%4===0}'),'checkpoint helper present');
ok(content.includes('DPP_TRIM_AGENT_TRACES_333(i)'),'trace byte trim wired');
ok(content.includes('t=262144'),'trace 256KB cap present');
ok(content.includes('status:`streaming`,text:``,toolExecutions:[],responseMessageId:null,collapsed:!1}),{persist:!1}'),'step start is memory-only');
ok(content.includes('status:`executing_tools`}),{persist:!1})'),'tool detected is memory-only');
ok(content.includes('{reasoning:r}),{persist:!1})'),'reasoning chunks are memory-only');
ok(content.includes('{text:r,...r?{status:`streaming`}:{}}),{persist:!1})'),'text chunks are memory-only');
ok(content.includes('r?{immediate:!0}:{persist:!1}'),'completed steps checkpoint only on cadence');
ok(content.includes('await D0(n)'),'loop completion still forces final persistence');
ok(content.includes('status:`error`,totalSteps:e.stepIndex,error:e.error}),{immediate:!0})'),'loop errors still force persistence');
ok(content.includes('DPP_DUPLICATE_TEXT_333(e.detail,e.output)'),'trace compaction dedupes result payload');
ok(content.includes('!DPP_DUPLICATE_TEXT_333(e.detail,e.output)&&t.push(`output:'),'agent DOM omits duplicate output');
ok(content.includes('o=t===null&&DPP_DUPLICATE_TEXT_333(e.result.detail,e.result.output)'),'model continuation omits duplicate output');
ok(content.includes('%APPDATA%\\obsidian\\obsidian.json'),'Obsidian config-first rule present');
ok(content.includes('DPP_STREAM_TERMINAL_331'),'3.3.1 stream-close logic preserved');
ok(content.includes('DPP_SAFE_DOM_332'),'3.3.2 Safe DOM preserved');
ok(bg.includes('function DPP_HISTORY_DUP_333'),'background history dedupe present');
ok(bg.includes('Math.min(Math.floor(e*O_),262144)'),'background tool history capped at 256KB');

// Evaluate the exact production content result-compaction helpers.
const compactSrc=between(content,'var jH=4e3','var UH=');
const ctx={JSON,String,Array,Object}; vm.createContext(ctx);
vm.runInContext(compactSrc+';globalThis.__LH=LH;globalThis.__dup=DPP_DUPLICATE_TEXT_333;',ctx);
const text='X'.repeat(5000)+'\r\nEND';
const detail=JSON.stringify([{type:'text',text}]);
const output=[{type:'text',text}];
let r=ctx.__LH({ok:true,summary:'ok',detail,output},{});
ok(r.output===undefined,'same ShunCode text is stored once even when detail is truncated');
ok(typeof r.detail==='string'&&r.detail.length<detail.length,'detail length cap still applies');
r=ctx.__LH({ok:true,summary:'ok',detail:'alpha',output:[{type:'text',text:'beta'}]},{});
ok(r.output!==undefined,'different text output is preserved');
r=ctx.__LH({ok:true,summary:'ok',detail:'artifact',output:{kind:'artifact',artifactId:'a1'}},{});
ok(r.output&&r.output.kind==='artifact','structured artifact output is preserved');
ok(ctx.__dup('same','same')===true&&ctx.__dup('a','b')===false,'plain text dedupe behavior');

// Evaluate exact production trace trim/checkpoint helpers.
const traceSrc=between(content,'function DPP_AGENT_TRACE_BYTES_333','function kU(');
const tctx={JSON,TextEncoder,Number}; vm.createContext(tctx);
vm.runInContext(traceSrc+';globalThis.__trim=DPP_TRIM_AGENT_TRACES_333;globalThis.__bytes=DPP_AGENT_TRACE_BYTES_333;',tctx);
const traces=Array.from({length:8},(_,i)=>({id:String(i),payload:'x'.repeat(50000)}));
const trimmed=tctx.__trim(traces,262144);
ok(trimmed.length<traces.length&&trimmed.at(-1).id==='7','trace cap drops oldest records and keeps newest');
ok(trimmed.length===1||tctx.__bytes(trimmed)<=262144,'trace cap respects byte budget unless one record alone exceeds it');

// Stress model: 19 results like the failing Obsidian run, 5 complete steps + error.
const oldResults=Array.from({length:19},(_,i)=>{const tx=`tool-${i}-`+'y'.repeat(2200);return {name:'run_command',result:{ok:true,summary:'MCP tool executed',detail:JSON.stringify([{type:'text',text:tx}]),output:[{type:'text',text:tx}]}}});
const newResults=oldResults.map(x=>({...x,result:ctx.__LH(x.result,{})}));
const oldTrace={steps:[{toolExecutions:oldResults}],finalText:'',error:''};
const newTrace={steps:[{toolExecutions:newResults}],finalText:'',error:''};
const oldBytes=Buffer.byteLength(JSON.stringify(oldTrace));
const newBytes=Buffer.byteLength(JSON.stringify(newTrace));
ok(newBytes<oldBytes*0.6,`19-tool trace payload materially reduced (${oldBytes} -> ${newBytes})`);
const oldWrites=6,newWrites=2; // 5 completed steps + error vs checkpoint-at-4 + error
ok(newBytes*newWrites<oldBytes*oldWrites*0.25,'estimated failing-run trace write amplification reduced by >75%');

// Background canonicalization helper must identify the same wrapper pair without treating objects as text.
const histSrc=between(bg,'function DPP_HISTORY_TEXT_333','function L_(');
const hctx={JSON,String,Array,Object};vm.createContext(hctx);
vm.runInContext(histSrc+';globalThis.__hdup=DPP_HISTORY_DUP_333;',hctx);
ok(hctx.__hdup(detail,output)===true,'background history recognizes duplicate ShunCode text');
ok(hctx.__hdup('artifact',{kind:'artifact'})===false,'background history does not collapse structured output');

console.log(`FIX333_AGENT_STABILITY_PASS ${pass}/${pass} oldBytes=${oldBytes} newBytes=${newBytes}`);
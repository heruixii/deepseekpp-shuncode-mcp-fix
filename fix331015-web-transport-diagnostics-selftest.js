const fs=require('fs'),vm=require('vm'),path=require('path');
const root=__dirname,main=fs.readFileSync(path.join(root,'content-scripts','main-world.js'),'utf8'),content=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8'),manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
let pass=0,total=0;function test(n,c){total++;if(!c){console.error('FAIL',n);process.exitCode=1}else{pass++;console.log('PASS',n)}}
test('version',['1.14.0.20','1.14.0.21','1.14.0.22','1.14.0.23','1.14.0.24','1.14.0.25','1.14.0.26','1.14.0.27','1.14.0.28','1.14.0.29','1.14.0.30','1.14.0.31','1.14.0.32','1.14.0.33','1.14.0.34','1.14.0.35','1.14.0.36','1.14.0.37','1.14.0.38','1.14.0.40'].includes(manifest.version));
test('version name',['1.14.0 ShunCode MCP Fix 3.3.10.15','1.14.0 ShunCode MCP Fix 3.3.10.16','1.14.0 ShunCode MCP Fix 3.3.10.17','1.14.0 ShunCode MCP Fix 3.3.10.18','1.14.0 ShunCode MCP Fix 3.3.10.19','1.14.0 ShunCode MCP Fix 3.3.10.20','1.14.0 ShunCode MCP Fix 3.3.10.21','1.14.0 ShunCode MCP Fix 3.3.10.22','1.14.0 ShunCode MCP Fix 3.3.10.23','1.14.0 ShunCode MCP Fix 3.3.10.24','1.14.0 ShunCode MCP Fix 3.3.10.25','1.14.0 ShunCode MCP Fix 3.3.10.26','1.14.0 ShunCode MCP Fix 3.3.10.27','1.14.0 ShunCode MCP Fix 3.3.10.28','1.14.0 ShunCode MCP Fix 3.3.10.29','1.14.0 ShunCode MCP Fix 3.3.10.30','1.14.0 ShunCode MCP Fix 3.3.10.31','1.14.0 ShunCode MCP Fix 3.3.10.32','1.14.0 ShunCode MCP Fix 3.3.10.33','1.14.0 ShunCode MCP Fix 3.3.10.35'].includes(manifest.version_name));
test('fetch request shape diagnostics',main.includes('dppRequestDiag331015:{route:a,rawBodyChars:n.body.length,augmentedBodyChars:'));
test('xhr request shape diagnostics',main.includes('v.dppRequestDiag331015={route:r,rawBodyChars:e.length,augmentedBodyChars:u.length'));
test('HTTP error passthrough',main.includes('phase:!i.ok?`http_error_passthrough`:`json_passthrough`'));
test('JSON passthrough',main.includes('a.toLowerCase().includes(`json`)'));
test('SSE byte counter',main.includes('p+=n.byteLength,m+=1'));
test('stream terminal state exported',main.includes('dppStreamFinished331015:n.finished===!0'));
test('fetch EOF diagnostics',main.includes('phase:`eof`,bytes:p,chunks:m,streamFinished:'));
test('fetch stream error diagnostics',main.includes('phase:`stream_error`,bytes:p,chunks:m'));
test('XHR load diagnostics',main.includes('phase:`xhr_load`,chars:n,streamFinished:'));
test('diagnostic ring key',content.includes('dpp_web_response_diag_331015'));
test('diagnostics persisted on request terminal',content.includes('await DPP_RECORD_WEB_DIAG_331015(e.payload),DPP_MANUAL_FINISH_334(t)'));
test('ring bounded after batching',content.includes('DPP_DIAG_BATCH_APPEND_331022(DPP_WEB_DIAG_KEY_331015,64,r)'));
test('diagnostics omit response/prompt/auth bodies',!content.includes('responseBody:')&&!content.includes('promptBody:')&&!content.includes('Authorization:typeof t')&&!content.includes('authorization:typeof t'));
test('3.3.10.14 DOM fix preserved',content.includes('function DPP_MUTATION_MESSAGES_331014'));
test('3.3.10.13 Agent delta preserved',content.includes('function DPP_AGENT_RESULT_DELTA_331013'));
const a=main.indexOf('async function to(e,t){'),b=main.indexOf('function no(e,t,n){',a);if(a<0||b<0)throw Error('fetch wrapper missing');const toSrc=main.slice(a,b),terminal=[];
const ctx={Response,Headers,TextDecoder,TextEncoder,ReadableStream,console,U:{onRequestTerminal:x=>terminal.push(x),onResponseComplete(){}},eo(){throw Error('eo should not run for passthrough')}};vm.createContext(ctx);vm.runInContext(toSrc+';globalThis.to=to;',ctx);
(async()=>{
 let r=new Response('{"error":"busy"}',{status:503,headers:{'content-type':'application/json'}}),out=await ctx.to(Promise.resolve(r),{requestId:'r1',dppRequestDiag331015:{route:'completion',rawBodyChars:10,augmentedBodyChars:20,descriptorCount:5,descriptorNames:['read_files']}});
 test('503 raw response preserved',out===r);test('503 status recorded',terminal.at(-1)?.diag331015?.httpStatus===503);test('503 phase recorded',terminal.at(-1)?.diag331015?.phase==='http_error_passthrough');
 let j=new Response('{"code":1}',{status:200,headers:{'content-type':'application/json'}});out=await ctx.to(Promise.resolve(j),{requestId:'r2',dppRequestDiag331015:{route:'completion'}});
 test('200 JSON raw response preserved',out===j);test('200 JSON phase recorded',terminal.at(-1)?.diag331015?.phase==='json_passthrough');
 console.log(`FIX331015_PASS ${pass}/${total}`);if(pass!==total)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

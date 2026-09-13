const fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
function range(a,b){let i=source.indexOf(a),j=source.indexOf(b,i+a.length);if(i<0||j<0)throw Error('range missing '+a);return source.slice(i,j)}
const code=range('function hI(){','var $I=')+range('async function qL(','function JL(');
const ctx={console,TextDecoder,TextEncoder,ReadableStream,Response,WeakMap,Map,Set,JSON,String,Object,Array,RegExp,Number,Math,Date,Promise,Wc:()=>null};vm.createContext(ctx);vm.runInContext(code+';globalThis.qL=qL;',ctx);
let pass=0,fail=0;function t(n,g,w){let ok=Object.is(g,w);console.log((ok?'PASS':'FAIL')+' '+n+' got='+JSON.stringify(g));ok?pass++:fail++}
function responseFrom(text){const bytes=new TextEncoder().encode(text);return new Response(new ReadableStream({start(c){c.enqueue(bytes);c.close()}}),{status:200,headers:{'content-type':'text/event-stream'}})}
(async()=>{
 let chunks=[];let r=await ctx.qL(responseFrom('data: {"o":"BATCH","v":[{"p":"response/content","o":"APPEND","v":"hello"},{"p":"response/status","v":"FINISHED"}]}\n\n'),{onTextChunk:(x)=>chunks.push(x)});t('nested-finish-production',r.finished,true);t('nested-content-production',chunks.join(''),'hello');
 chunks=[];r=await ctx.qL(responseFrom('data: {"o":"BATCH","v":[{"p":"response/content","o":"APPEND","v":"old"},{"p":"quasi_status","v":"FINISHED"}]}\n\n'),{onTextChunk:(x)=>chunks.push(x)});t('legacy-quasi-finish-production',r.finished,true);t('legacy-content-production',chunks.join(''),'old');
 chunks=[];r=await ctx.qL(responseFrom('data: {"p":"response/content","o":"APPEND","v":"partial-secret"}\n\n'),{onTextChunk:(x)=>chunks.push(x)});t('abrupt-eof-stays-incomplete',r.finished,false);t('abrupt-content-preserved',chunks.join(''),'partial-secret');t('abrupt-diag-no-content',JSON.stringify(r.dppStreamEvents).includes('partial-secret'),false);t('abrupt-diag-has-path',r.dppStreamEvents.some(x=>x.p==='response/content'),true);
 if(fail)process.exit(1);console.log('FIX33_STREAM_INTEGRATION_PASS '+pass);
})().catch(e=>{console.error(e);process.exit(1)});
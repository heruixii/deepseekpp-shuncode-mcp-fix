const fs=require('fs'),path=require('path'),vm=require('vm');
const source=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
function range(a,b){const i=source.indexOf(a),j=source.indexOf(b,i+a.length);if(i<0||j<0)throw Error('range missing '+a);return source.slice(i,j)}
const code=range('function hI(){','var $I=')+range('async function qL(','function JL(');
const ctx={console,TextDecoder,TextEncoder,ReadableStream,Response,WeakMap,Map,Set,JSON,String,Object,Array,RegExp,Number,Math,Date,Promise,Wc:()=>null};vm.createContext(ctx);vm.runInContext(code+';globalThis.qL=qL;globalThis.UI=UI;globalThis.DPP_STREAM_ERROR_331=DPP_STREAM_ERROR_331;globalThis.DPP_STREAM_TERMINAL_331=DPP_STREAM_TERMINAL_331;',ctx);
let pass=0,fail=0;function t(n,g,w){const ok=Object.is(g,w);console.log((ok?'PASS':'FAIL')+' '+n+' got='+JSON.stringify(g));ok?pass++:fail++}
function responseFrom(text){const bytes=new TextEncoder().encode(text);return new Response(new ReadableStream({start(c){c.enqueue(bytes);c.close()}}),{status:200,headers:{'content-type':'text/event-stream'}})}
(async()=>{
 t('helper-finished-still-valid',ctx.UI({p:'response/status',v:'FINISHED'},{type:'message'}),true);
 t('helper-benign-close',ctx.UI({status:'ok'},{type:'close'}),true);
 t('helper-close-failed-status',ctx.UI({p:'response/status',v:'FAILED'},{type:'close'}),false);
 t('helper-close-error-object',ctx.UI({error:{message:'boom'}},{type:'close'}),false);
 t('helper-message-not-terminal',ctx.UI({status:'ok'},{type:'message'}),false);
 t('helper-error-false-not-error',ctx.DPP_STREAM_ERROR_331({error:false}),false);
 let s='event: ready\ndata: {}\n\n'+'event: update_file\ndata: {"path":"x"}\n\n'+'event: hint\ndata: {"text":"done"}\n\n'+'event: close\ndata: {"status":"ok"}\n\n';
 let r=await ctx.qL(responseFrom(s),{});t('production-real-sequence-finishes',r.finished,true);t('production-real-sequence-markers',r.dppStreamEvents.map(x=>x.event).join('>'),'ready>update_file>hint>close');
 r=await ctx.qL(responseFrom('event: close\ndata: {"p":"response/status","v":"FAILED"}\n\n'),{});t('production-failed-close-incomplete',r.finished,false);
 r=await ctx.qL(responseFrom('event: close\ndata: {"error":{"message":"boom"}}\n\n'),{});t('production-error-close-incomplete',r.finished,false);
 r=await ctx.qL(responseFrom('data: {"p":"response/content","o":"APPEND","v":"partial"}\n\n'),{});t('production-bare-eof-still-incomplete',r.finished,false);
 r=await ctx.qL(responseFrom('data: {"o":"BATCH","v":[{"p":"response/status","v":"FINISHED"}]}\n\n'),{});t('production-old-finished-still-works',r.finished,true);
 if(fail){console.error(`FIX331_STREAM_CLOSE_FAIL pass=${pass} fail=${fail}`);process.exit(1)}
 console.log(`FIX331_STREAM_CLOSE_PASS ${pass}`);
})().catch(e=>{console.error(e);process.exit(1)});
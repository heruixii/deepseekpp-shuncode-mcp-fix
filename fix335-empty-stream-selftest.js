const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||path.resolve(__dirname);
const src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');
let pass=0;function ok(x,n){if(!x){console.error('FAIL',n);process.exit(1)}pass++;console.log('PASS',n)}
function between(a,b){const i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error('missing '+a);return src.slice(i,j)}
const code=between('var DPP_FRESH_POW_RETRY_335','function VR(')+between('async function HR(','function UR(');
async function make({wl}){
 let auth=0,pow=0,wlCount=0,delay=0;
 const ctx={console,AbortController,DOMException,zR:2,
   BL(){auth++;return {Authorization:'redacted-'+auth}},
   async LL(){pow++;return {'X-DS-PoW-Response':'pow-'+pow}},
   IR(){return {signal:new AbortController().signal,timedOut:()=>false,clear(){}}},
   async LR(){delay++},
   async WL(req,opt,signal){wlCount++;return wl(req,opt,signal,wlCount)},
   globalThis:null};ctx.globalThis=ctx;vm.createContext(ctx);vm.runInContext(code+';globalThis.BR_=BR;globalThis.HR_=HR;',ctx);
 const submit=ctx.BR_({powWasmUrl:'x'});
 return {ctx,submit,counts:()=>({auth,pow,wlCount,delay})};
}
(async()=>{
 ok(src.includes('DPP_FRESH_POW_RETRY_335'),'fresh-pow marker present');
 ok(src.includes('dppStreamBytes+=o?.byteLength??0'),'raw byte diagnostics wired');
 ok(src.includes('Stream diagnostics:'),'privacy-safe stream diagnostics surfaced');
 ok(src.includes('if(a)throw e'),'partial-output exception is not replayed');
 // Empty first attempt -> fresh request/PoW second attempt -> success.
 let m=await make({wl:async(req,opt,signal,n)=> n===1?{finished:false,responseMessageId:null,requestMessageId:null,assistantText:'',dppStreamEvents:[],dppHttpStatus:200,dppContentType:'text/event-stream',dppStreamBytes:0,dppStreamChunks:0}:{finished:true,responseMessageId:42,requestMessageId:41,assistantText:'ok',dppStreamEvents:[{event:'close'}],dppHttpStatus:200,dppContentType:'text/event-stream',dppStreamBytes:25,dppStreamChunks:1}});
 let r=await m.submit({chatSessionId:'s',parentMessageId:1,modelType:'x',prompt:'p',refFileIds:[],thinkingEnabled:false,searchEnabled:false},{onTextChunk(){},onReasoningChunk(){}});
 let c=m.counts();ok(r.finished===true,'empty first attempt recovers');ok(c.auth===2&&c.pow===2,'retry refreshes auth and PoW');ok(c.wlCount===2,'exactly two completion attempts');ok(r.streamDiagnostics.attempt===2&&r.streamDiagnostics.freshPow===true,'diagnostics mark fresh-PoW retry');
 // Network failure before any output -> fresh second request.
 m=await make({wl:async(req,opt,signal,n)=>{if(n===1)throw Error('network');return {finished:true,responseMessageId:2,requestMessageId:1,assistantText:'',dppStreamEvents:[],dppHttpStatus:200,dppContentType:'text/event-stream',dppStreamBytes:10,dppStreamChunks:1}}});
 r=await m.submit({chatSessionId:'s',parentMessageId:1,modelType:'x',prompt:'p',refFileIds:[],thinkingEnabled:false,searchEnabled:false},{onTextChunk(){},onReasoningChunk(){}});c=m.counts();ok(r.finished===true,'pre-output network failure recovers');ok(c.pow===2&&c.wlCount===2,'network retry also gets fresh PoW');
 // Partial output + exception must not replay.
 m=await make({wl:async(req,opt,signal,n)=>{opt.onTextChunk('partial','partial');throw Error('stream broke')}});
 let threw=false;try{await m.submit({chatSessionId:'s',parentMessageId:1,modelType:'x',prompt:'p',refFileIds:[],thinkingEnabled:false,searchEnabled:false},{onTextChunk(){},onReasoningChunk(){}})}catch(e){threw=true}
 c=m.counts();ok(threw,'partial stream error surfaces');ok(c.wlCount===1&&c.pow===1,'partial stream is never replayed');
 // Two empty attempts remain bounded and return diagnostics.
 m=await make({wl:async()=>({finished:false,responseMessageId:null,requestMessageId:null,assistantText:'',dppStreamEvents:[],dppHttpStatus:200,dppContentType:'text/event-stream',dppStreamBytes:0,dppStreamChunks:0})});
 r=await m.submit({chatSessionId:'s',parentMessageId:1,modelType:'x',prompt:'p',refFileIds:[],thinkingEnabled:false,searchEnabled:false},{onTextChunk(){},onReasoningChunk(){}});c=m.counts();ok(r.finished===false,'two empty attempts remain incomplete');ok(c.wlCount===2&&c.pow===2,'empty recovery stays bounded at two attempts');ok(r.streamDiagnostics.bytes===0&&r.streamDiagnostics.chunks===0&&r.streamDiagnostics.httpStatus===200,'empty response diagnostics preserved');
 ok(!JSON.stringify(r.streamDiagnostics).match(/Authorization|prompt|pow-/),'diagnostics contain no auth/prompt/PoW secret');
 console.log(`FIX335_EMPTY_STREAM_PASS ${pass}/${pass}`);
})().catch(e=>{console.error(e);process.exit(1)});
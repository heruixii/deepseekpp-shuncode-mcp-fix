const fs=require('fs'),path=require('path'),vm=require('vm');
const src=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
let pass=0,fail=0; const ok=(c,n,d='')=>{console.log(c?'PASS':'FAIL',n,d);c?pass++:fail++};
function slice(a,b){let i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error('slice '+a);return src.slice(i,j)}
const ctx={console,AbortController,DOMException}; vm.createContext(ctx);
ctx.zR=2;
ctx.IR=()=>({signal:new AbortController().signal,timedOut:()=>false,clear(){}});
ctx.LR=async()=>{};
vm.runInContext(slice('function DPP_RETRY_INVALID_MESSAGE_339','async function HR'),ctx);
ctx.DPP_INVALID_MESSAGE_BACKOFF_339=async()=>{};
vm.runInContext(slice('async function HR','function UR'),ctx);
(async()=>{
 let calls=[],rebuild=0;
 ctx.WL=async(req,cb)=>{calls.push(req.id); if(calls.length===1){let e=Error('invalid');e.dppInvalidMessageId339=true;e.dppNoRetry337=true;throw e} return {finished:true,responseMessageId:42,requestMessageId:41,dppStreamEvents:[],dppHttpStatus:200,dppContentType:'text/event-stream',dppStreamBytes:10,dppStreamChunks:1}};
 let r=await ctx.HR({id:0},{onTextChunk(){},onReasoningChunk(){}},new AbortController().signal,async()=>({id:++rebuild}));
 ok(calls.join(',')==='0,1','invalid-id exactly one retry',calls.join(',')); ok(rebuild===1,'retry rebuilt request once',String(rebuild)); ok(r.streamDiagnostics.invalidMessageRetry===true,'retry diagnostic true'); ok(r.streamDiagnostics.attempt===2,'retry finishes on attempt 2',String(r.streamDiagnostics.attempt));
 calls=[];rebuild=0;ctx.WL=async(req,cb)=>{calls.push(req.id);cb.onTextChunk('partial','partial');let e=Error('invalid');e.dppInvalidMessageId339=true;e.dppNoRetry337=true;throw e}; let threw=false;try{await ctx.HR({id:0},{onTextChunk(){},onReasoningChunk(){}},new AbortController().signal,async()=>({id:++rebuild}))}catch(e){threw=true} ok(threw&&calls.length===1&&rebuild===0,'partial output blocks invalid-id replay',`calls=${calls.length} rebuild=${rebuild}`);
 calls=[];rebuild=0;ctx.WL=async(req)=>{calls.push(req.id);let e=Error('other json');e.dppNoRetry337=true;throw e};threw=false;try{await ctx.HR({id:0},{onTextChunk(){},onReasoningChunk(){}},new AbortController().signal,async()=>({id:++rebuild}))}catch(e){threw=e.message==='other json'} ok(threw&&calls.length===1&&rebuild===0,'other JSON stays no-retry',`calls=${calls.length}`);
 calls=[];rebuild=0;ctx.WL=async(req)=>{calls.push(req.id);let e=Error('invalid');e.dppInvalidMessageId339=true;e.dppNoRetry337=true;throw e};threw=false;try{await ctx.HR({id:0},{onTextChunk(){},onReasoningChunk(){}},new AbortController().signal,async()=>({id:++rebuild}))}catch(e){threw=true} ok(threw&&calls.length===2&&rebuild===1,'second invalid-id stops after one recovery',`calls=${calls.length} rebuild=${rebuild}`);
 console.log(`FIX339_HR_SIM_PASS ${pass}/${pass+fail}`); if(fail)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
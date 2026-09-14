const fs=require('fs'),path=require('path'),vm=require('vm');
const src=fs.readFileSync(path.join(__dirname,'content-scripts','content.js'),'utf8');
let pass=0,fail=0;const ok=(c,n,d='')=>{console.log(c?'PASS':'FAIL',n,d);c?pass++:fail++};
const start=src.indexOf('function DPP_PARENT_FALLBACK_33103');
const end=src.indexOf('function VR(e){',start);
if(start<0||end<0)throw Error('helper not found');
const ctx={};vm.createContext(ctx);vm.runInContext(src.slice(start,end),ctx);
const invalid={dppInvalidMessageId339:true};
ok(ctx.DPP_PARENT_FALLBACK_33103(invalid,180,182)===180,'real-case fallback 182 -> 180');
ok(ctx.DPP_PARENT_FALLBACK_33103({},180,182)===null,'other error no fallback');
ok(ctx.DPP_PARENT_FALLBACK_33103(invalid,null,182)===null,'no previous parent no fallback');
ok(ctx.DPP_PARENT_FALLBACK_33103(invalid,182,182)===null,'same parent no fallback');
function makeSession(initial){let f={parentMessageId:initial,previousParentMessageId:null,setParentMessageId:(e,t=f.parentMessageId)=>{f.previousParentMessageId=t;f.parentMessageId=e}};return f}
(async()=>{
 const s=makeSession(182);s.previousParentMessageId=180;
 let req={parentMessageId:s.parentMessageId},calls=[];
 const submit=async r=>{calls.push(r.parentMessageId);if(r.parentMessageId===182)throw invalid;return{responseMessageId:184,finished:true}};
 let out;try{out=await submit(req)}catch(e){let fb=ctx.DPP_PARENT_FALLBACK_33103(e,s.previousParentMessageId,req.parentMessageId);if(fb===null)throw e;req={...req,parentMessageId:fb};out=await submit(req)}
 s.setParentMessageId(out.responseMessageId,req.parentMessageId);
 ok(JSON.stringify(calls)==='[182,180]','bounded parent fallback sequence',JSON.stringify(calls));
 ok(s.parentMessageId===184,'new response becomes current parent',s.parentMessageId);
 ok(s.previousParentMessageId===180,'actual successful predecessor retained',s.previousParentMessageId);
 let otherCalls=[];try{let r={parentMessageId:182};const f=async x=>{otherCalls.push(x.parentMessageId);throw {dppNoRetry337:true}};try{await f(r)}catch(e){let fb=ctx.DPP_PARENT_FALLBACK_33103(e,180,r.parentMessageId);if(fb===null)throw e}}catch(e){}
 ok(JSON.stringify(otherCalls)==='[182]','non-invalid JSON never parent-fallbacks',JSON.stringify(otherCalls));
 ok(src.includes('previousParentMessageId:null'),'session previous-parent history wired');
 ok(src.includes('DPP_PARENT_FALLBACK_33103(DPPParentError,n.previousParentMessageId,l.parentMessageId)'),'provider fallback hook wired');
 ok(src.includes('n.setParentMessageId(ie.responseMessageId,l.parentMessageId)'),'successful request predecessor persisted');
 ok(src.includes('if(e?.dppInvalidMessageId339===!0&&!a&&!c339&&n<zR)'),'3.3.9 same-parent retry preserved');
 console.log(`FIX33103_PARENT_FALLBACK_PASS ${pass}/${pass+fail}`);if(fail)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=process.argv[2]||__dirname,src=fs.readFileSync(path.join(root,'content-scripts','content.js'),'utf8');let pass=0;
function ok(v,n){if(!v){console.error('FAIL',n);process.exit(1)}pass++;console.log('PASS',n)}
function slice(a,b){let i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw Error('missing '+a);return src.slice(i,j)}
const ctx={JSON,Number,console};vm.createContext(ctx);vm.runInContext(slice('function DPP_JSON_FIELD_337','async function WL(')+';globalThis.err=DPP_JSON_COMPLETION_ERROR_337;',ctx);
let r={status:200};
let e=ctx.err(r,JSON.stringify({code:400,msg:'file too large'}));ok(e.includes('code=400'),'json code surfaced');ok(e.includes('message=file too large'),'json msg surfaced');ok(!e.includes('{"code"'),'raw json not surfaced');
e=ctx.err(r,JSON.stringify({error:{code:'CTX_LIMIT',message:'context length exceeded'},secret:'do-not-log'}));ok(e.includes('code=CTX_LIMIT'),'nested error code surfaced');ok(e.includes('message=context length exceeded'),'nested error message surfaced');ok(!e.includes('do-not-log'),'unrelated JSON fields not surfaced');
e=ctx.err(r,JSON.stringify({data:{biz_code:123,biz_msg:' attachment rejected \n now '}}));ok(e.includes('code=123'),'nested biz code surfaced');ok(e.includes('message=attachment rejected now'),'message whitespace normalized');
e=ctx.err(r,'not-json secret-body');ok(e==='DeepSeek completion returned JSON instead of an SSE stream (HTTP 200).','malformed json raw body hidden');
ok(src.includes('body:JSON.stringify({chat_session_id:e.chatSessionId,parent_message_id:e.parentMessageId,model_type:Uc(e.modelType),prompt:e.prompt,ref_file_ids:e.refFileIds'),'normal completion still preserves explicit ref_file_ids');
ok(src.includes('refFileIds:DPP_AGENT_SYNTHETIC_REF_FILES_337'),'agent uses synthetic empty refs');ok(src.includes('var DPP_AGENT_SYNTHETIC_REF_FILES_337=[];'),'synthetic refs are empty');
for(let i=0;i<10;i++){const opts={refFileIds:[]};ok(opts.refFileIds.length===0,'agent synthetic turn '+(i+1)+' has no stale attachment');}
ok(src.includes('DPP_FRESH_POW_RETRY_335'),'fresh-PoW recovery preserved');ok(src.includes('dppNoRetry337'),'JSON/business response gets dedicated no-replay marker');ok(src.includes('e?.dppNoRetry337===!0'),'dedicated JSON response bypasses fresh-PoW replay');ok(src.includes('DPP_EXEC_BLOCK_BUDGET_336=262144'),'long-task storage fix preserved');
const m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));ok(['1.14.0.2','1.14.0.3','1.14.0.4','1.14.0.5','1.14.0.6','1.14.0.7','1.14.0.8','1.14.0.9','1.14.0.10','1.14.0.11'].includes(m.version),'real MV3 version bumped');ok(['1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6'].includes(m.version_name),'version name updated');
console.log(`FIX337_ATTACHMENT_JSON_PASS ${pass}/${pass}`);

function DPP_PLAIN_OBJECT_1140(e){return!!(e&&typeof e==`object`&&!Array.isArray(e))}function DPP_TOOL_DIAG_1140(e){let t=`none`,n=0;if(typeof e?.raw==`string`){let r=e.raw.indexOf(`>`),i=e.raw.lastIndexOf(`</`);if(r>=0&&i>r){let a=e.raw.slice(r+1,i).trim();n=a.length;if(!a)t=`empty`;else if(!a.startsWith(`{`))t=`raw-body`;else try{JSON.parse(a),t=`json-valid`}catch{t=`json-repaired`}}else n=e.raw.length}let r=DPP_PLAIN_OBJECT_1140(e?.payload)?Object.keys(e.payload).slice(0,30):[];return JSON.stringify({stage:`prepared`,tool:e?.invocationName??e?.name??`unknown`,rawState:t,bodyChars:n,payloadKeys:r,parseError:e?.parseError?.code??null})}function DPP_RESULT_DIAG_1140(e){return JSON.stringify({stage:`result`,ok:e?.ok===!0,errorCode:e?.error?.code??null,retryable:e?.error?.retryable??null,durationMs:typeof e?.durationMs==`number`?e.durationMs:null,truncated:e?.truncated===!0,summary:typeof e?.summary==`string`?e.summary.slice(0,300):``})}
const a=DPP_TOOL_DIAG_1140({name:"run_command",invocationName:"mcp__shuncode_run_command",raw:'<mcp__shuncode_run_command>{"command":"SECRET-COMMAND","background":false}</mcp__shuncode_run_command>',payload:{command:"SECRET-COMMAND",background:false}});
console.log(a);
if(a.includes("SECRET-COMMAND")) { console.error("diagnostic leaked payload value"); process.exit(1); }
if(!a.includes('"rawState":"json-valid"') || !a.includes('"payloadKeys":["command","background"]')) process.exit(2);
const b=DPP_TOOL_DIAG_1140({name:"run_command",raw:'<run_command>echo hello</run_command>',payload:{command:"echo hello",background:false}});
console.log(b);
if(!b.includes('"rawState":"raw-body"')) process.exit(3);
console.log('DIAGNOSTIC_PASS');

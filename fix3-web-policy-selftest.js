const NR=120000,PR=250,FR=900;
function DPP_WEB_BASE_3(e){let t=String(e?.invocationName??e?.name??``).toLowerCase().split(/[.:/]/).pop();return t.replace(/^mcp_+[^_]+_/,``)}function DPP_WEB_SAFE_RETRY_3(e,t){if(t?.ok!==!1||t?.error?.retryable!==!0||t?.error?.details?.externalOutcome===`ambiguous`)return!1;let n=DPP_WEB_BASE_3(e);return!/(run_command|shell_exec|shell_session_exec|apply_patch|write|create|delete|remove|update|edit|patch|move|rename|send|post|put|install|upload|commit|push|merge|execute|exec|run)/.test(n)&&/(read|list|find|search|grep|query|get|status|health|check|stat|snapshot|fetch|lookup|describe|discover|inspect|preview|history)/.test(n)}async function DPP_WEB_RETRY_DELAY_3(){await new Promise(e=>setTimeout(e,220))}
function DPP_MODEL_RESULT_BUDGET_3(e){let t=String(e??``).toLowerCase();return/status|health|check|stat|ping/.test(t)?6e3:/read|list|find|search|grep|snapshot|fetch|get/.test(t)?12e3:/run|exec|shell|build|test/.test(t)?16e3:9e3}function DPP_ERROR_CLASS_3(e){let t=String(e?.code??`unknown`);return t===`dpp_fix3_no_progress`?{stage:`loop_guard`,action:`change_tool_or_parameters`}:/^tool_call_/.test(t)?{stage:`format_or_schema`,action:`repair_parameters`}:/^tool_authorization|authorization/.test(t)?{stage:`authorization`,action:`refresh_authorization`}:/^mcp_(http|sse|connect|initialize|transport|response)/.test(t)?{stage:`mcp_transport`,action:e?.retryable===!0?`safe_retry_if_read_only`:`inspect_connection`}:/^mcp_tool|tool_unsupported/.test(t)?{stage:`mcp_tool`,action:`refresh_tool_catalog`}:{stage:`tool_runtime`,action:e?.retryable===!0?`retry_if_safe`:`inspect_error`}}
function DPP_STABLE_3(e){if(e===null||typeof e!=`object`)return JSON.stringify(e);if(Array.isArray(e))return`[${e.map(DPP_STABLE_3).join(`,`)}]`;return`{${Object.keys(e).sort().map(t=>`${JSON.stringify(t)}:${DPP_STABLE_3(e[t])}`).join(`,`)}}`}
function Hz(e=``){let t=String(e).toLowerCase(),n=/继续.*直到.*完成|直到.*完成|彻底完成|until.*complete|until.*done|finish.*everything/.test(t)?128:/代码|文件|项目|修复|汉化|仓库|构建|测试|code|file|project|fix|repo|build|test/.test(t)?96:88;return{maxSteps:n,maxNudges:8,stepTimeoutMs:NR,requestDelayMinMs:PR,requestDelayMaxMs:FR,fullToolResultWindow:4}}

let failed=0;function ok(n,c,d=''){console.log(`${c?'PASS':'FAIL'} ${n}${d?' '+d:''}`);if(!c)failed++}
ok('retry-read',DPP_WEB_SAFE_RETRY_3({name:'read_file'},{ok:false,error:{retryable:true,code:'mcp_http_error'}})===true);
ok('retry-list-namespaced',DPP_WEB_SAFE_RETRY_3({invocationName:'mcp__shuncode_list_directory'},{ok:false,error:{retryable:true,code:'mcp_http_error'}})===true);
ok('no-retry-run',DPP_WEB_SAFE_RETRY_3({invocationName:'mcp__shuncode_run_command'},{ok:false,error:{retryable:true,code:'mcp_http_error'}})===false);
ok('no-retry-patch',DPP_WEB_SAFE_RETRY_3({name:'apply_patch'},{ok:false,error:{retryable:true,code:'mcp_http_error'}})===false);
ok('no-retry-ambiguous',DPP_WEB_SAFE_RETRY_3({name:'read_file'},{ok:false,error:{retryable:true,details:{externalOutcome:'ambiguous'}}})===false);
ok('budget-status',DPP_MODEL_RESULT_BUDGET_3('health_status')===6000);
ok('budget-read',DPP_MODEL_RESULT_BUDGET_3('read_file')===12000);
ok('budget-run',DPP_MODEL_RESULT_BUDGET_3('run_command')===16000);
ok('budget-default',DPP_MODEL_RESULT_BUDGET_3('weird_tool')===9000);
let ec=DPP_ERROR_CLASS_3({code:'mcp_http_error',retryable:true});ok('error-mcp-transport',ec.stage==='mcp_transport'&&ec.action==='safe_retry_if_read_only');
ec=DPP_ERROR_CLASS_3({code:'tool_call_payload_invalid',retryable:false});ok('error-format-schema',ec.stage==='format_or_schema');
ec=DPP_ERROR_CLASS_3({code:'dpp_fix3_no_progress',retryable:false});ok('error-loop',ec.stage==='loop_guard');
ok('step-default',Hz('hello').maxSteps===88);
ok('step-project',Hz('修复这个项目').maxSteps===96);
ok('step-until-done',Hz('继续直到完成').maxSteps===128);
let a={b:2,a:1},b={a:1,b:2};ok('stable-key-order',DPP_STABLE_3(a)===DPP_STABLE_3(b));
const source=require('fs').readFileSync(require('path').join(__dirname,'content-scripts','content.js'),'utf8');
ok('guard-runtime-hook',source.includes('d.count>=4')&&source.includes('dpp_fix3_no_progress'));
ok('retry-runtime-hook',source.includes('DPP_WEB_SAFE_RETRY_3(i,o)'));
ok('dynamic-budget-runtime-hook',source.includes('Ce=Hz(t.originalPrompt)'));
ok('dynamic-result-runtime-hook',source.includes('DPP_MODEL_RESULT_BUDGET_3(e.name)')&&source.includes('contextCompacted:'));
ok('capability-window-runtime-hook',source.includes('DPP_CAPABILITY_WINDOW_32')&&source.includes('capabilityWindow:t'));
if(failed)process.exit(1);console.log(`ALL_PASS ${21}`);

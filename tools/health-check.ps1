param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
function Fail([string]$m){Write-Host "FAIL $m"; exit 1}
function Pass([string]$m){Write-Host "PASS $m"}
if(-not (Test-Path -LiteralPath $Root)){Fail "root missing: $Root"}
$manifest=Join-Path $Root 'manifest.json'
& python -c "import json,pathlib,sys; r=pathlib.Path(sys.argv[1]); files=['manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json']; objs=[json.loads((r/f).read_text(encoding='utf-8-sig')) for f in files]; assert objs[0].get('version_name')=='1.14.0 ShunCode MCP Fix 3.3.10.6'; assert objs[0].get('version')=='1.14.0.11'" $Root
if($LASTEXITCODE -ne 0){Fail 'UTF-8 JSON validation'}else{Pass 'UTF-8 JSON manifest/locales'}
if(Test-Path -LiteralPath (Join-Path $Root '_metadata')){Fail '_metadata should be absent'}else{Pass '_metadata absent'}
$js=Get-ChildItem -LiteralPath $Root -Recurse -File -Filter *.js
foreach($f in $js){& node --check $f.FullName *> $null;if($LASTEXITCODE -ne 0){Fail "JS syntax $($f.FullName)"}}
Pass "JS syntax $($js.Count) files"
$tests=@('mcp-repair-selftest.js','mcp-diagnostic-selftest.js','fix3-policy-selftest.js','fix3-web-policy-selftest.js','fix3-continuation-selftest.js','fix31-agent-selftest.js','fix32-capability-selftest.js','fix33-known-issues-selftest.js','fix33-stream-integration-selftest.js','fix331-stream-close-selftest.js','fix332-safe-dom-selftest.js','fix333-agent-stability-selftest.js','fix334-tool-storm-selftest.js','fix335-empty-stream-selftest.js','fix336-long-task-stability-selftest.js','fix337-attachment-json-selftest.js','fix338-agent-budget-selftest.js','fix339-message-id-selftest.js','fix339-hr-sim-selftest.js','fix3310-dsml-storm-selftest.js','fix33101-quarantine-selftest.js','fix33102-manual-page-filter-selftest.js','fix33103-parent-fallback-selftest.js','fix33104-history-filter-selftest.js','fix33105-prompt-exposure-selftest.js','fix33106-dsml-eof-selftest.js','fix33106-dsml-eof-integration-selftest.js')
foreach($t in $tests){$p=Join-Path $Root $t;if(-not(Test-Path $p)){Fail "missing selftest $t"};& node $p;if($LASTEXITCODE -ne 0){Fail "selftest $t"};Pass "selftest $t"}
$bg=[IO.File]::ReadAllText((Join-Path $Root 'background.js'))
$policy=[IO.File]::ReadAllText((Join-Path $Root 'fix3-policy.js'))
$content=[IO.File]::ReadAllText((Join-Path $Root 'content-scripts\content.js'))
$main=[IO.File]::ReadAllText((Join-Path $Root 'content-scripts\main-world.js'))
$markers=@(
 @('policy import',$bg,'importScripts(chrome.runtime.getURL(`fix3-policy.js`))'),
 @('adaptive routing',$bg,'DPP_FIX3?.routeBonus'),
 @('recent success',$bg,'DPP_FIX3?.recordSuccess'),
 @('background safe retry',$bg,'DPP_FIX3?.shouldRetry'),
 @('model-only compaction',$bg,'compactResult?.(e.name,e.result)'),
 @('health enrichment',$bg,'healthFromCache?.(i)'),
 @('web safe retry',$content,'DPP_WEB_SAFE_RETRY_3(i,o)'),
 @('web dynamic result budget',$content,'DPP_MODEL_RESULT_BUDGET_3'),
 @('web loop guard',$content,'dpp_fix3_no_progress'),
 @('web dynamic steps',$content,'Ce=Hz(t.originalPrompt)'),
 @('continuation cues',$content,'DPP_MIDSTEP_CUE_31'),
 @('nudge hard cap',$content,'y.count>=Ce.maxNudges?[]'),
 @('progress-sensitive nudge reset',$content,'DPP_HAS_PROGRESS_31(_);'),
 @('fix31 helper definitions',$content,'function DPP_TOOL_BASE_31'),
 @('completion gate',$content,'DPP_COMPLETION_GATE_31(g)'),
 @('ambiguous verify-before-retry',$content,'verify_before_retry'),
 @('capability window preservation',$content,'DPP_CAPABILITY_WINDOW_32'),
 @('capability rediscover action',$content,'rediscover_capability'),
 @('fix33 recursive stream finish',$content,'function DPP_STREAM_FINISHED_33'),
 @('fix331 sse close terminal',$content,'function DPP_STREAM_TERMINAL_331'),
 @('fix331 close failure guard',$content,'function DPP_STREAM_ERROR_331'),
 @('fix332 safe dom marker',$content,'DPP_SAFE_DOM_332'),
 @('fix333 agent checkpoint',$content,'DPP_AGENT_CHECKPOINT_333'),
 @('fix333 trace byte cap',$content,'DPP_TRIM_AGENT_TRACES_333'),
 @('fix333 result dedupe',$content,'DPP_DUPLICATE_TEXT_333'),
 @('fix333 history dedupe',$bg,'DPP_HISTORY_DUP_333'),
 @('fix333 obsidian discovery',$content,'[Fix 3.3.3 targeted discovery]'),
 @('fix334 manual tool storm guard',$content,'DPP_MANUAL_TOOL_LIMIT_334'),
 @('fix334 trace read migration',$content,'n.length!==e.length&&await t.writeAfterReadAlreadyLocked(n)'),
 @('fix334 startup trace migration',$content,'ZV(),await jX(),JX(k0()),t()&&'),
 @('fix334 auth limit classification',$content,'stop_tool_calls_and_summarize'),
 @('fix334 command sanity',$content,'DPP_COMMAND_SANITY_334'),
 @('fix334 authorization safety net',$bg,'DPP_AUTH_CALL_LIMIT_334'),
 @('fix335 fresh pow retry',$content,'DPP_FRESH_POW_RETRY_335'),
 @('fix335 stream byte diagnostics',$content,'dppStreamBytes+=o?.byteLength??0'),
 @('fix335 stream diagnostics surface',$content,'Stream diagnostics:'),
 @('fix335 partial stream no replay',$content,'if(a)throw e'),
 @('fix336 execution block byte cap',$content,'DPP_EXEC_BLOCK_BUDGET_336=262144'),
 @('fix336 execution block migration',$content,'DPP_TRIM_EXEC_BLOCKS_336(e)'),
 @('fix336 observer self-filter',$content,'DPP_AGENT_OBSERVER_IGNORABLE_336'),
 @('fix336 reasoning throttle',$content,'DPP_REASONING_RAF_336=requestAnimationFrame'),
 @('fix336 history startup trim',$bg,'DPP_TRIM_TOOL_HISTORY_ON_START_336().catch'),
 @('fix337 synthetic attachment refs',$content,'DPP_AGENT_SYNTHETIC_REF_FILES_337=[]'),
 @('fix337 json response parser',$content,'DPP_JSON_COMPLETION_ERROR_337'),
 @('fix337 json no replay',$content,'e?.dppNoRetry337===!0'),
 @('fix338 min agent budget',$content,'DPP_AGENT_MIN_BUDGET_338=88'),
 @('fix338 project agent budget',$content,'DPP_AGENT_PROJECT_BUDGET_338=96'),
 @('fix338 completion agent budget',$content,'DPP_AGENT_COMPLETION_BUDGET_338=128'),
 @('fix339 ranked message id',$content,'function DPP_MESSAGE_ID_SET_339'),
 @('fix339 invalid message recognizer',$content,'function DPP_INVALID_MESSAGE_ID_339'),
 @('fix339 bounded invalid message retry',$content,'function DPP_RETRY_INVALID_MESSAGE_339'),
 @('fix339 invalid message backoff',$content,'function DPP_INVALID_MESSAGE_BACKOFF_339'),
 @('fix3310 control noise filter',$content,'function DPP_CONTROL_NOISE_FILTER_3310'),
 @('fix3310 markup storm limit',$content,'DPP_CONTROL_NOISE_LIMIT_3310=24'),
 @('fix3310 cross-format signature',$content,'function DPP_TOOL_SIGNATURE_3310'),
 @('fix3310 fallback legacy dedupe',$content,'fallback-legacy'),
 @('fix33101 quarantine state',$content,'DPPControlQuarantine=!1'),
 @('fix33101 no fatal storm throw',$content,'if(DPPControlQuarantine)return;'),
 @('fix33102 manual page line filter',$main,'function DPP_PAGE_CONTROL_LINE_33102'),
 @('fix33102 manual page split prefix',$main,'function DPP_PAGE_CONTROL_PREFIX_33102'),
 @('fix33102 manual page filter wiring',$main,'DPP_PAGE_CONTROL_FILTER_33102(a,this.toolInvocationNameSet,this.controlNoiseFenceState)'),
 @('fix33103 parent fallback helper',$content,'function DPP_PARENT_FALLBACK_33103'),
 @('fix33103 previous parent history',$content,'previousParentMessageId:null'),
 @('fix33103 provider parent fallback',$content,'DPP_PARENT_FALLBACK_33103(DPPParentError,n.previousParentMessageId,l.parentMessageId)'),
 @('fix33104 history filter helper',$main,'function DPP_HISTORY_CONTROL_FILTER_33104'),
 @('fix33104 history fragment filter',$main,'function DPP_HISTORY_FRAGMENT_FILTER_33104'),
 @('fix33104 assistant history wiring',$main,'Pr(e)&&(e.content=DPP_HISTORY_CONTROL_FILTER_33104(e.content,n))'),
 @('fix33105 prompt exposure policy',$policy,'function promptExposureSettings('),
 @('fix33105 descriptor cost policy',$policy,'function promptDescriptorCost('),
 @('fix33105 background exposure wiring',$bg,'promptExposureSettings?.(n,r,t)??r'),
 @('fix33105 obsidian run route',$policy,'file&&note&&/(run_command|shell|exec|run)/.test(n)'),
 @('fix33106 dsml eof salvage',$main,'function DPP_DSML_EOF_SALVAGE_33106'),
 @('fix33106 synth finish guard',$main,'function DPP_SHOULD_SYNTH_FINISH_33106'),
 @('fix33106 finish frame',$main,'function DPP_FINISH_FRAME_33106'),
 @('fix33106 Fa recovery wiring',$main,'recoveredDsml33106:t'),
 @('fix33106 eo synthetic finish wiring',$main,'DPP_SHOULD_SYNTH_FINISH_33106(n.finished,DPPRecoveredDsml,n.responseMessageId)'),
 @('fix33 safe eof retry',$content,'!s.finished&&!a&&s.responseMessageId==null&&s.requestMessageId==null&&n<zR'),
 @('fix33 stream diagnostics',$content,'Last stream markers:'),
 @('fix33 utf8 guard',$content,'function DPP_WINDOWS_ENCODING_GUARD_33'),
 @('fix33 common preflight',$content,'DPP_COMMON_PREFLIGHT_33(e)'),
 @('fix33 pty direct recovery',$content,'DPP_SHOULD_DIRECT_RETRY_33'),
 @('fix33 workspace hint',$content,'function DPP_RESULT_HINT_33'),
 @('fix33 prompt safety rules',$content,'DPP_AGENT_RULES_33'),
 @('schema compiler content',$content,'working_directory`,'),
 @('schema compiler main',$main,'working_directory`,')
)
foreach($x in $markers){if(-not $x[1].Contains($x[2])){Fail "marker $($x[0])"}else{Pass "marker $($x[0])"}}
& python -m py_compile (Join-Path $Root 'tools\apply-fix3.py');$pyCompileCode=$LASTEXITCODE; if($pyCompileCode -ne 0){Fail 'apply-fix3.py compile'}else{Pass 'apply-fix3.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix31.py');$pyCompile31Code=$LASTEXITCODE; if($pyCompile31Code -ne 0){Fail 'apply-fix31.py compile'}else{Pass 'apply-fix31.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix32.py');$pyCompile32Code=$LASTEXITCODE; if($pyCompile32Code -ne 0){Fail 'apply-fix32.py compile'}else{Pass 'apply-fix32.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33.py');$pyCompile33Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33Code -ne 0){Fail 'apply-fix33.py compile'}else{Pass 'apply-fix33.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix331.py');$pyCompile331Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile331Code -ne 0){Fail 'apply-fix331.py compile'}else{Pass 'apply-fix331.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix332.py');$pyCompile332Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile332Code -ne 0){Fail 'apply-fix332.py compile'}else{Pass 'apply-fix332.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix333.py');$pyCompile333Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile333Code -ne 0){Fail 'apply-fix333.py compile'}else{Pass 'apply-fix333.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix334.py');$pyCompile334Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile334Code -ne 0){Fail 'apply-fix334.py compile'}else{Pass 'apply-fix334.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix335.py');$pyCompile335Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile335Code -ne 0){Fail 'apply-fix335.py compile'}else{Pass 'apply-fix335.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix336.py');$pyCompile336Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile336Code -ne 0){Fail 'apply-fix336.py compile'}else{Pass 'apply-fix336.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix337.py');$pyCompile337Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile337Code -ne 0){Fail 'apply-fix337.py compile'}else{Pass 'apply-fix337.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix338.py');$pyCompile338Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile338Code -ne 0){Fail 'apply-fix338.py compile'}else{Pass 'apply-fix338.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix339.py');$pyCompile339Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile339Code -ne 0){Fail 'apply-fix339.py compile'}else{Pass 'apply-fix339.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix3310.py');$pyCompile3310Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile3310Code -ne 0){Fail 'apply-fix3310.py compile'}else{Pass 'apply-fix3310.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33101.py');$pyCompile33101Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33101Code -ne 0){Fail 'apply-fix33101.py compile'}else{Pass 'apply-fix33101.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33102.py');$pyCompile33102Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33102Code -ne 0){Fail 'apply-fix33102.py compile'}else{Pass 'apply-fix33102.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33103.py');$pyCompile33103Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33103Code -ne 0){Fail 'apply-fix33103.py compile'}else{Pass 'apply-fix33103.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33104.py');$pyCompile33104Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33104Code -ne 0){Fail 'apply-fix33104.py compile'}else{Pass 'apply-fix33104.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33105.py');$pyCompile33105Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33105Code -ne 0){Fail 'apply-fix33105.py compile'}else{Pass 'apply-fix33105.py compile'}
& python -m py_compile (Join-Path $Root 'tools\apply-fix33106.py');$pyCompile33106Code=$LASTEXITCODE; Get-ChildItem -LiteralPath (Join-Path $Root 'tools') -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if($pyCompile33106Code -ne 0){Fail 'apply-fix33106.py compile'}else{Pass 'apply-fix33106.py compile'}
Write-Host "HEALTH_CHECK_PASS root=$Root js=$($js.Count)"

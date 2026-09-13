param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
function Fail([string]$m){Write-Host "FAIL $m"; exit 1}
function Pass([string]$m){Write-Host "PASS $m"}
if(-not (Test-Path -LiteralPath $Root)){Fail "root missing: $Root"}
$manifest=Join-Path $Root 'manifest.json'
& python -c "import json,pathlib,sys; r=pathlib.Path(sys.argv[1]); files=['manifest.json','_locales/en/messages.json','_locales/zh_CN/messages.json']; objs=[json.loads((r/f).read_text(encoding='utf-8-sig')) for f in files]; assert objs[0].get('version_name')=='1.14.0 ShunCode MCP Fix 3.3.4'" $Root
if($LASTEXITCODE -ne 0){Fail 'UTF-8 JSON validation'}else{Pass 'UTF-8 JSON manifest/locales'}
if(Test-Path -LiteralPath (Join-Path $Root '_metadata')){Fail '_metadata should be absent'}else{Pass '_metadata absent'}
$js=Get-ChildItem -LiteralPath $Root -Recurse -File -Filter *.js
foreach($f in $js){& node --check $f.FullName *> $null;if($LASTEXITCODE -ne 0){Fail "JS syntax $($f.FullName)"}}
Pass "JS syntax $($js.Count) files"
$tests=@('mcp-repair-selftest.js','mcp-diagnostic-selftest.js','fix3-policy-selftest.js','fix3-web-policy-selftest.js','fix3-continuation-selftest.js','fix31-agent-selftest.js','fix32-capability-selftest.js','fix33-known-issues-selftest.js','fix33-stream-integration-selftest.js','fix331-stream-close-selftest.js','fix332-safe-dom-selftest.js','fix333-agent-stability-selftest.js','fix334-tool-storm-selftest.js')
foreach($t in $tests){$p=Join-Path $Root $t;if(-not(Test-Path $p)){Fail "missing selftest $t"};& node $p;if($LASTEXITCODE -ne 0){Fail "selftest $t"};Pass "selftest $t"}
$bg=[IO.File]::ReadAllText((Join-Path $Root 'background.js'))
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
 @('fix33 safe eof retry',$content,'s=!o.finished&&!i&&o.responseMessageId==null&&o.requestMessageId==null&&n<zR'),
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
Write-Host "HEALTH_CHECK_PASS root=$Root js=$($js.Count)"

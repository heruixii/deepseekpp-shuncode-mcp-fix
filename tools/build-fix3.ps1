param(
  [Parameter(Mandatory=$true)][string]$Source,
  [Parameter(Mandatory=$true)][string]$Destination,
  [string]$ZipPath = '',
  [switch]$Force
)
$ErrorActionPreference='Stop'
$TemplateRoot=Split-Path -Parent $PSScriptRoot
$Apply=Join-Path $PSScriptRoot 'apply-fix3.py'
$Apply31=Join-Path $PSScriptRoot 'apply-fix31.py'
$Apply32=Join-Path $PSScriptRoot 'apply-fix32.py'
$Apply33=Join-Path $PSScriptRoot 'apply-fix33.py'
$Apply331=Join-Path $PSScriptRoot 'apply-fix331.py'
$Apply332=Join-Path $PSScriptRoot 'apply-fix332.py'
$Apply333=Join-Path $PSScriptRoot 'apply-fix333.py'
$Apply334=Join-Path $PSScriptRoot 'apply-fix334.py'
$Apply335=Join-Path $PSScriptRoot 'apply-fix335.py'
$Apply336=Join-Path $PSScriptRoot 'apply-fix336.py'
$Apply337=Join-Path $PSScriptRoot 'apply-fix337.py'
$Apply338=Join-Path $PSScriptRoot 'apply-fix338.py'
$Apply339=Join-Path $PSScriptRoot 'apply-fix339.py'
$Apply3310=Join-Path $PSScriptRoot 'apply-fix3310.py'
$Apply33101=Join-Path $PSScriptRoot 'apply-fix33101.py'
$Apply33102=Join-Path $PSScriptRoot 'apply-fix33102.py'
$Apply33103=Join-Path $PSScriptRoot 'apply-fix33103.py'
$Apply33104=Join-Path $PSScriptRoot 'apply-fix33104.py'
$Apply33105=Join-Path $PSScriptRoot 'apply-fix33105.py'
$Apply33106=Join-Path $PSScriptRoot 'apply-fix33106.py'
$Apply33107=Join-Path $PSScriptRoot 'apply-fix33107.py'
$Apply33108=Join-Path $PSScriptRoot 'apply-fix33108.py'
$Apply33109=Join-Path $PSScriptRoot 'apply-fix33109.py'
$Apply331010=Join-Path $PSScriptRoot 'apply-fix331010.py'
$Apply331011=Join-Path $PSScriptRoot 'apply-fix331011.py'
$Health=Join-Path $PSScriptRoot 'health-check.ps1'
function Full([string]$p){return [IO.Path]::GetFullPath($p).TrimEnd('\')}
$src=Full $Source;$dst=Full $Destination
if($src -eq $dst){throw 'Source and Destination must be different.'}
if(-not(Test-Path -LiteralPath $src -PathType Container)){throw "Source does not exist: $src"}
if(Test-Path -LiteralPath $dst){if(-not $Force){throw "Destination already exists: $dst. Use -Force only when intentional."};Remove-Item -LiteralPath $dst -Recurse -Force}
if($ZipPath){$zip=Full $ZipPath;if(Test-Path $zip){if(-not $Force){throw "Zip already exists: $zip. Use -Force only when intentional."};Remove-Item -LiteralPath $zip -Force}}else{$zip=''}
$built=$false
try{
  Copy-Item -LiteralPath $src -Destination $dst -Recurse
  $sourceManifest=Get-Content -LiteralPath (Join-Path $src 'manifest.json') -Raw | ConvertFrom-Json
  $sourceVersion=[string]$sourceManifest.version_name
  $currentOverlaySource=$sourceVersion -in @('1.14.0 ShunCode MCP Fix 3.3.2','1.14.0 ShunCode MCP Fix 3.3.3','1.14.0 ShunCode MCP Fix 3.3.4','1.14.0 ShunCode MCP Fix 3.3.5','1.14.0 ShunCode MCP Fix 3.3.6','1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7','1.14.0 ShunCode MCP Fix 3.3.10.8','1.14.0 ShunCode MCP Fix 3.3.10.9','1.14.0 ShunCode MCP Fix 3.3.10.10','1.14.0 ShunCode MCP Fix 3.3.10.11')
  if(-not $currentOverlaySource){
    & python $Apply $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix3.py failed with exit $LASTEXITCODE"}
    & python $Apply31 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix31.py failed with exit $LASTEXITCODE"}
    & python $Apply32 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix32.py failed with exit $LASTEXITCODE"}
    & python $Apply33 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33.py failed with exit $LASTEXITCODE"}
    & python $Apply331 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix331.py failed with exit $LASTEXITCODE"}
    & python $Apply332 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix332.py failed with exit $LASTEXITCODE"}
  }else{
    Write-Host "BUILD_FIX3 current-overlay source detected: $sourceVersion; legacy overlays skipped"
  }
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.8','1.14.0 ShunCode MCP Fix 3.3.10.9','1.14.0 ShunCode MCP Fix 3.3.10.10','1.14.0 ShunCode MCP Fix 3.3.10.11')){
  if((-not $currentOverlaySource) -or $sourceVersion -eq '1.14.0 ShunCode MCP Fix 3.3.2'){
    & python $Apply333 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix333.py failed with exit $LASTEXITCODE"}
  }
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.5','1.14.0 ShunCode MCP Fix 3.3.6','1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply334 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix334.py failed with exit $LASTEXITCODE"}
    & python $Apply335 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix335.py failed with exit $LASTEXITCODE"}
  }
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.6','1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply336 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix336.py failed with exit $LASTEXITCODE"}
  }
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.7','1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply337 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix337.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.7+ source detected; Fix 3.3.7 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.8','1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply338 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix338.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.8+ source detected; Fix 3.3.8 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.9','1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply339 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix339.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.9+ source detected; Fix 3.3.9 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10','1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply3310 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix3310.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10+ source detected; Fix 3.3.10 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.1','1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33101 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33101.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.1+ source detected; Fix 3.3.10.1 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.2','1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33102 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33102.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.2+ source detected; Fix 3.3.10.2 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.3','1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33103 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33103.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.3+ source detected; Fix 3.3.10.3 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.4','1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33104 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33104.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.4+ source detected; Fix 3.3.10.4 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.5','1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33105 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33105.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.5+ source detected; Fix 3.3.10.5 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.6','1.14.0 ShunCode MCP Fix 3.3.10.7')){
    & python $Apply33106 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33106.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.6+ source detected; Fix 3.3.10.6 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.7','1.14.0 ShunCode MCP Fix 3.3.10.8')){
    & python $Apply33107 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33107.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.7+ source detected; Fix 3.3.10.7 overlay skipped'}
  & python $Apply33108 $dst
  if($LASTEXITCODE -ne 0){throw "apply-fix33108.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.8+ source detected; earlier overlays skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.9','1.14.0 ShunCode MCP Fix 3.3.10.10','1.14.0 ShunCode MCP Fix 3.3.10.11')){
    & python $Apply33109 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix33109.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.9+ source detected; Fix 3.3.10.9 overlay skipped'}
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.10.10','1.14.0 ShunCode MCP Fix 3.3.10.11')){
    & python $Apply331010 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix331010.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.10 source detected; current overlay skipped'}
  if($sourceVersion -ne '1.14.0 ShunCode MCP Fix 3.3.10.11'){
    & python $Apply331011 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix331011.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.10.11 source detected; current overlay skipped'}
  foreach($name in @('mcp-repair-selftest.js','mcp-diagnostic-selftest.js','fix3-policy-selftest.js','fix3-web-policy-selftest.js','fix3-continuation-selftest.js','fix31-agent-selftest.js','fix32-capability-selftest.js','fix33-known-issues-selftest.js','fix33-stream-integration-selftest.js','fix331-stream-close-selftest.js','fix332-safe-dom-selftest.js','fix333-agent-stability-selftest.js','fix334-tool-storm-selftest.js','fix335-empty-stream-selftest.js','fix336-long-task-stability-selftest.js','fix337-attachment-json-selftest.js','fix338-agent-budget-selftest.js','fix339-message-id-selftest.js','fix339-hr-sim-selftest.js','fix3310-dsml-storm-selftest.js','fix33101-quarantine-selftest.js','fix33102-manual-page-filter-selftest.js','fix33103-parent-fallback-selftest.js','fix33104-history-filter-selftest.js','fix33105-prompt-exposure-selftest.js','fix33106-dsml-eof-selftest.js','fix33106-dsml-eof-integration-selftest.js','fix33107-agent-lifecycle-mcp503-selftest.js','fix33108-lifecycle-selftest.js','fix33109-global-trace-stats-selftest.js','fix331010-status-errors-selftest.js','fix331011-resume-crash-selftest.js')){
    Copy-Item -LiteralPath (Join-Path $TemplateRoot $name) -Destination (Join-Path $dst $name) -Force
  }
  foreach($name in @('README.md','README-SHUNCODE-FIX3.md','FIX3-TEST-REPORT.md')){
    $doc=Join-Path $TemplateRoot $name
    if(Test-Path -LiteralPath $doc){Copy-Item -LiteralPath $doc -Destination (Join-Path $dst $name) -Force}
  }
  $destTools=Join-Path $dst 'tools';New-Item -ItemType Directory -Force -Path $destTools|Out-Null
  foreach($name in @('apply-fix3.py','apply-fix31.py','apply-fix32.py','apply-fix33.py','apply-fix331.py','apply-fix332.py','apply-fix333.py','apply-fix334.py','apply-fix335.py','apply-fix336.py','apply-fix337.py','apply-fix338.py','apply-fix339.py','apply-fix3310.py','apply-fix33101.py','apply-fix33102.py','apply-fix33103.py','apply-fix33104.py','apply-fix33105.py','apply-fix33106.py','apply-fix33107.py','apply-fix33108.py','apply-fix33109.py','apply-fix331010.py','apply-fix331011.py','health-check.ps1','build-fix3.ps1')){
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $destTools $name) -Force
  }
  Get-ChildItem -LiteralPath $dst -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $destTools 'health-check.ps1') -Root $dst
  if($LASTEXITCODE -ne 0){throw "Fix3 health check failed with exit $LASTEXITCODE"}
  if($zip){$parent=Split-Path -Parent $zip;if($parent -and -not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null};Add-Type -AssemblyName System.IO.Compression.FileSystem;[System.IO.Compression.ZipFile]::CreateFromDirectory($dst,$zip,[System.IO.Compression.CompressionLevel]::Optimal,$false)}
  $built=$true
  Write-Host "BUILD_FIX3_PASS destination=$dst zip=$zip"
}catch{
  if(Test-Path -LiteralPath $dst){Remove-Item -LiteralPath $dst -Recurse -Force -ErrorAction SilentlyContinue}
  if($zip -and (Test-Path -LiteralPath $zip)){Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue}
  Write-Error "BUILD_FIX3_FAILED; incomplete output removed. $($_.Exception.Message)"
  exit 1
}
if(-not $built){exit 1}

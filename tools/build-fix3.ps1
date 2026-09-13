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
  $currentOverlaySource=$sourceVersion -in @('1.14.0 ShunCode MCP Fix 3.3.2','1.14.0 ShunCode MCP Fix 3.3.3','1.14.0 ShunCode MCP Fix 3.3.4','1.14.0 ShunCode MCP Fix 3.3.5','1.14.0 ShunCode MCP Fix 3.3.6')
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
  if((-not $currentOverlaySource) -or $sourceVersion -eq '1.14.0 ShunCode MCP Fix 3.3.2'){
    & python $Apply333 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix333.py failed with exit $LASTEXITCODE"}
  }
  if($sourceVersion -notin @('1.14.0 ShunCode MCP Fix 3.3.5','1.14.0 ShunCode MCP Fix 3.3.6')){
    & python $Apply334 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix334.py failed with exit $LASTEXITCODE"}
    & python $Apply335 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix335.py failed with exit $LASTEXITCODE"}
  }
  if($sourceVersion -ne '1.14.0 ShunCode MCP Fix 3.3.6'){
    & python $Apply336 $dst
    if($LASTEXITCODE -ne 0){throw "apply-fix336.py failed with exit $LASTEXITCODE"}
  }else{Write-Host 'BUILD_FIX3 Fix 3.3.6 source detected; current overlay skipped'}
  foreach($name in @('mcp-repair-selftest.js','mcp-diagnostic-selftest.js','fix3-policy-selftest.js','fix3-web-policy-selftest.js','fix3-continuation-selftest.js','fix31-agent-selftest.js','fix32-capability-selftest.js','fix33-known-issues-selftest.js','fix33-stream-integration-selftest.js','fix331-stream-close-selftest.js','fix332-safe-dom-selftest.js','fix333-agent-stability-selftest.js','fix334-tool-storm-selftest.js','fix335-empty-stream-selftest.js','fix336-long-task-stability-selftest.js')){
    Copy-Item -LiteralPath (Join-Path $TemplateRoot $name) -Destination (Join-Path $dst $name) -Force
  }
  foreach($name in @('README.md','README-SHUNCODE-FIX3.md','FIX3-TEST-REPORT.md')){
    $doc=Join-Path $TemplateRoot $name
    if(Test-Path -LiteralPath $doc){Copy-Item -LiteralPath $doc -Destination (Join-Path $dst $name) -Force}
  }
  $destTools=Join-Path $dst 'tools';New-Item -ItemType Directory -Force -Path $destTools|Out-Null
  foreach($name in @('apply-fix3.py','apply-fix31.py','apply-fix32.py','apply-fix33.py','apply-fix331.py','apply-fix332.py','apply-fix333.py','apply-fix334.py','apply-fix335.py','apply-fix336.py','health-check.ps1','build-fix3.ps1')){
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $destTools $name) -Force
  }
  Get-ChildItem -LiteralPath $dst -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $destTools 'health-check.ps1') -Root $dst
  if($LASTEXITCODE -ne 0){throw "Fix3 health check failed with exit $LASTEXITCODE"}
  if($zip){$parent=Split-Path -Parent $zip;if($parent -and -not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null};Compress-Archive -Path (Join-Path $dst '*') -DestinationPath $zip -CompressionLevel Optimal}
  $built=$true
  Write-Host "BUILD_FIX3_PASS destination=$dst zip=$zip"
}catch{
  if(Test-Path -LiteralPath $dst){Remove-Item -LiteralPath $dst -Recurse -Force -ErrorAction SilentlyContinue}
  if($zip -and (Test-Path -LiteralPath $zip)){Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue}
  Write-Error "BUILD_FIX3_FAILED; incomplete output removed. $($_.Exception.Message)"
  exit 1
}
if(-not $built){exit 1}
param(
 [string]$IdentityName,
 [string]$Publisher,
 [string]$PublisherDisplayName = 'Nova',
 [string]$Version = '1.0.17.0',
 [switch]$Preview
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
if ($Preview) {
 if (-not $IdentityName) { $IdentityName = 'SaturnServerLauncher.Preview' }
 if (-not $Publisher) { $Publisher = 'CN=SaturnDevelopment' }
} elseif (-not $IdentityName -or -not $Publisher) {
 throw 'IdentityName and Publisher must be copied from Partner Center. Use -Preview only for a non-submittable build.'
}
python -m pip install -r store/requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
python store/generate_assets.py
if ($LASTEXITCODE -ne 0) { throw 'Asset generation failed.' }
python -m PyInstaller --noconfirm --clean --distpath store-output --workpath store-work store/Saturn.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
$AppFolder = Join-Path $Root 'store-output/Saturn'
Copy-Item store/Assets $AppFolder -Recurse -Force
$ManifestArgs = @('store/generate_manifest.py','--output',"$AppFolder/AppxManifest.xml",'--name',$IdentityName,'--publisher',$Publisher,'--display',$PublisherDisplayName,'--version',$Version)
if ($Preview) { $ManifestArgs += '--preview' }
python @ManifestArgs
if ($LASTEXITCODE -ne 0) { throw 'Manifest generation failed.' }
# Smoke test uses isolated preferences, never a maintainer's real profiles.
$OldLocalData = $env:LOCALAPPDATA
$env:LOCALAPPDATA = Join-Path $Root 'store-work/smoke-state'
try {
 $Smoke = Start-Process -FilePath "$AppFolder/Saturn.exe" -ArgumentList '--smoke-test' -PassThru
 if (-not $Smoke.WaitForExit(90000)) { $Smoke.Kill(); throw 'Frozen app smoke test timed out.' }
 if ($Smoke.ExitCode -ne 0) { throw 'Frozen app smoke test failed. See store-work/smoke-state/MCServerSwitcher/app.log.' }
 $Result = Get-Content "$env:LOCALAPPDATA/MCServerSwitcher/store-smoke.json" | ConvertFrom-Json
 if (-not $Result.store -or -not $Result.qml) { throw 'Frozen smoke test did not confirm bundled Store mode and QML.' }
} finally { $env:LOCALAPPDATA = $OldLocalData }
$Sdk = "${env:ProgramFiles(x86)}/Windows Kits/10/bin"
$MakeAppx = Get-ChildItem "$Sdk/*/x64/makeappx.exe" | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $MakeAppx) { throw 'Install Windows SDK including MakeAppx.' }
$Suffix = if ($Preview) { '-PREVIEW-UNSIGNED' } else { '-STORE-SUBMISSION' }
$Package = Join-Path $Root "store-output/Saturn-$Version-x64$Suffix.msix"
& $MakeAppx.FullName pack /d $AppFolder /p $Package /o
if ($LASTEXITCODE -ne 0) { throw 'MakeAppx validation or packaging failed.' }
$Hash = (Get-FileHash $Package -Algorithm SHA256).Hash.ToLower()
"$Hash  $(Split-Path $Package -Leaf)" | Set-Content store-output/SHA256SUMS.txt
Write-Host "Created $Package"
Write-Host 'Unsigned: Store submission will be signed by Microsoft after certification. Preview identity is not submittable.'

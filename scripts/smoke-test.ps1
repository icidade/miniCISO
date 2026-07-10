[CmdletBinding()]
param([switch]$Online)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$profiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'profiles') -Directory | Sort-Object Name
$hermes = Get-Command hermes -ErrorAction Stop
$profileList = (& $hermes.Source profile list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'hermes profile list failed.' }

foreach ($profile in $profiles) {
    if ($profileList -notmatch [regex]::Escape($profile.Name)) {
        throw "Profile not registered in Hermes: $($profile.Name)"
    }
    $installedSoul = Join-Path $HOME ".hermes\profiles\$($profile.Name)\SOUL.md"
    if (-not (Test-Path -LiteralPath $installedSoul)) {
        throw "SOUL.md not installed: $($profile.Name)"
    }
    Write-Host "OK: $($profile.Name)"

    if ($Online) {
        & $hermes.Source -p $profile.Name chat -Q -q 'Answer in one line starting with OK and state your role in MiniCISO.'
        if ($LASTEXITCODE -ne 0) { throw "Online smoke test failed: $($profile.Name)" }
    }
}

Write-Host "Smoke test completed for $($profiles.Count) profiles." -ForegroundColor Green

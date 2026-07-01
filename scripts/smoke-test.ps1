[CmdletBinding()]
param([switch]$Online)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$profiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'profiles') -Directory | Sort-Object Name
$hermes = Get-Command hermes -ErrorAction Stop
$profileList = (& $hermes.Source profile list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'hermes profile list falhou.' }

foreach ($profile in $profiles) {
    if ($profileList -notmatch [regex]::Escape($profile.Name)) {
        throw "Perfil não registrado no Hermes: $($profile.Name)"
    }
    $installedSoul = Join-Path $HOME ".hermes\profiles\$($profile.Name)\SOUL.md"
    if (-not (Test-Path -LiteralPath $installedSoul)) {
        throw "SOUL.md não instalado: $($profile.Name)"
    }
    Write-Host "OK: $($profile.Name)"

    if ($Online) {
        & $hermes.Source -p $profile.Name chat -Q -q 'Responda em uma linha começando com OK e informe seu papel no MiniCISO.'
        if ($LASTEXITCODE -ne 0) { throw "Smoke test online falhou: $($profile.Name)" }
    }
}

Write-Host "Smoke test concluído para $($profiles.Count) perfis." -ForegroundColor Green

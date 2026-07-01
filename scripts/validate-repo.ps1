[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$errors = [Collections.Generic.List[string]]::new()

function Add-ValidationError([string]$Message) {
    $script:errors.Add($Message)
}

$requiredFiles = @(
    'README.md', 'INSTALL.md', 'LICENSE', 'SECURITY.md', '.env.example',
    'config/hermes-version.env', 'config/tooling-dependencies.example.yaml',
    'scripts/bootstrap.ps1', 'scripts/bootstrap.sh',
    'scripts/smoke-test.ps1', 'scripts/smoke-test.sh',
    'scripts/validate-repo.ps1', 'scripts/validate-repo.sh',
    'meta/MANIFEST.json', 'meta/SUMMARY.json'
)
foreach ($relative in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relative))) {
        Add-ValidationError "Arquivo obrigatório ausente: $relative"
    }
}

$profiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'profiles') -Directory -ErrorAction SilentlyContinue
if ($profiles.Count -ne 9) {
    Add-ValidationError "Esperados 9 diretórios de perfil; encontrados $($profiles.Count)."
}
foreach ($profile in $profiles) {
    $soul = Join-Path $profile.FullName 'SOUL.md'
    if (-not (Test-Path -LiteralPath $soul) -or (Get-Item -LiteralPath $soul).Length -eq 0) {
        Add-ValidationError "SOUL.md ausente ou vazio: $($profile.Name)"
    }
}

$versionPath = Join-Path $repoRoot 'config/hermes-version.env'
if (Test-Path -LiteralPath $versionPath) {
    $versionText = Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8
    if ($versionText -notmatch '(?m)^HERMES_TAG=v\d{4}\.\d{1,2}\.\d{1,2}\r?$') {
        Add-ValidationError 'HERMES_TAG não tem o formato esperado.'
    }
    if ($versionText -notmatch '(?m)^HERMES_COMMIT=[0-9a-f]{40}\r?$') {
        Add-ValidationError 'HERMES_COMMIT deve ser um SHA Git completo.'
    }
    if (($versionText | Select-String -Pattern '(?m)^HERMES_INSTALL_(PS1|SH)_SHA256=[A-F0-9]{64}\r?$' -AllMatches).Matches.Count -ne 2) {
        Add-ValidationError 'Os dois checksums de instalador devem ser SHA-256 completos.'
    }
}

$strictUtf8 = New-Object Text.UTF8Encoding($false, $true)
$textExtensions = @('.md', '.json', '.yaml', '.yml', '.sh', '.ps1', '.env', '.example', '.gitattributes', '.gitignore')
$textFiles = Get-ChildItem -LiteralPath $repoRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch '[\\/]\.git[\\/]' -and
    ($textExtensions -contains $_.Extension -or $_.Name -in @('.gitignore', '.gitattributes'))
}
foreach ($file in $textFiles) {
    try { [void]$strictUtf8.GetString([IO.File]::ReadAllBytes($file.FullName)) }
    catch { Add-ValidationError "UTF-8 inválido: $($file.FullName.Substring($repoRoot.Length + 1))" }
}

$secretPattern = '-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}'
foreach ($file in $textFiles) {
    if (Select-String -LiteralPath $file.FullName -Pattern $secretPattern -Quiet) {
        Add-ValidationError "Possível segredo encontrado: $($file.FullName.Substring($repoRoot.Length + 1))"
    }
}

foreach ($json in @('meta/MANIFEST.json', 'meta/SUMMARY.json')) {
    try { Get-Content -LiteralPath (Join-Path $repoRoot $json) -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null }
    catch { Add-ValidationError "JSON inválido: $json" }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ -ErrorAction Continue }
    throw "Validação falhou com $($errors.Count) erro(s)."
}

Write-Host "OK: estrutura válida, $($profiles.Count) perfis, UTF-8 e verificações básicas de segredo." -ForegroundColor Green

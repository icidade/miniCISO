[CmdletBinding()]
param(
    [string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }),
    [string]$WorkspaceRoot = $(Join-Path $HOME 'miniciso-security'),
    [switch]$SkipHermesInstall,
    [switch]$SkipProviderSetup
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$versionFile = Join-Path $repoRoot 'config\hermes-version.env'

function Read-VersionFile {
    param([string]$Path)
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match '^([A-Z0-9_]+)=(.+)$') {
            $values[$matches[1]] = $matches[2].Trim()
        }
    }
    return $values
}

function Invoke-Hermes {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $script:HermesCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Hermes falhou: hermes $($Arguments -join ' ')"
    }
}

function Resolve-HermesCommand {
    $command = Get-Command hermes -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $candidates = @(
        (Join-Path $HermesHome 'bin\hermes.exe'),
        (Join-Path $HermesHome 'bin\hermes.cmd'),
        (Join-Path $HermesHome 'bin\hermes.ps1'),
        (Join-Path $HOME '.local\bin\hermes.exe'),
        (Join-Path $HOME '.local\bin\hermes.cmd'),
        (Join-Path $HOME '.local\bin\hermes.ps1')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw 'Comando hermes não encontrado após a instalação. Abra um novo terminal e execute novamente com -SkipHermesInstall.'
}

if (-not (Test-Path -LiteralPath $versionFile)) {
    throw "Arquivo de versão ausente: $versionFile"
}
$version = Read-VersionFile -Path $versionFile
$requiredVersionKeys = @('HERMES_COMMIT', 'HERMES_TAG', 'HERMES_INSTALL_PS1_SHA256')
foreach ($key in $requiredVersionKeys) {
    if (-not $version.ContainsKey($key)) { throw "Chave ausente em hermes-version.env: $key" }
}

Write-Host "MiniCISO: Hermes $($version.HERMES_TAG) ($($version.HERMES_COMMIT))"

if (-not $SkipHermesInstall) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $installerUri = "https://raw.githubusercontent.com/NousResearch/hermes-agent/$($version.HERMES_COMMIT)/scripts/install.ps1"
    $installerPath = Join-Path ([IO.Path]::GetTempPath()) "hermes-install-$($version.HERMES_COMMIT).ps1"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $installerUri -OutFile $installerPath
        $actualHash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash
        if ($actualHash -ne $version.HERMES_INSTALL_PS1_SHA256) {
            throw "Checksum inválido para o instalador Hermes. Esperado $($version.HERMES_INSTALL_PS1_SHA256), recebido $actualHash"
        }

        $installDir = Join-Path $HermesHome 'hermes-agent'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath `
            -Commit $version.HERMES_COMMIT `
            -HermesHome $HermesHome `
            -InstallDir $installDir `
            -SkipSetup `
            -NonInteractive
        if ($LASTEXITCODE -ne 0) { throw "Instalador Hermes terminou com código $LASTEXITCODE" }
    }
    finally {
        Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
    }
}

$env:Path = "$(Join-Path $HermesHome 'bin');$(Join-Path $HOME '.local\bin');$env:Path"
$script:HermesCommand = Resolve-HermesCommand

if (-not $SkipProviderSetup) {
    Write-Host 'Configure o provedor/modelo local. Nenhuma credencial será gravada no repo.'
    Invoke-Hermes -Arguments @('setup')
}

$profileRoot = Join-Path $HOME '.hermes\profiles'
$profiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'profiles') -Directory | Sort-Object Name
if ($profiles.Count -ne 9) { throw "Esperados 9 perfis; encontrados $($profiles.Count)." }

foreach ($profile in $profiles) {
    $name = $profile.Name
    $destinationDir = Join-Path $profileRoot $name
    if (-not (Test-Path -LiteralPath $destinationDir)) {
        Write-Host "Criando perfil $name"
        Invoke-Hermes -Arguments @('profile', 'create', $name, '--clone')
    }

    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    $sourceSoul = Join-Path $profile.FullName 'SOUL.md'
    $destinationSoul = Join-Path $destinationDir 'SOUL.md'
    if ((Test-Path -LiteralPath $destinationSoul) -and
        ((Get-FileHash $sourceSoul).Hash -ne (Get-FileHash $destinationSoul).Hash)) {
        Copy-Item -LiteralPath $destinationSoul -Destination "$destinationSoul.pre-miniciso" -Force
    }
    Copy-Item -LiteralPath $sourceSoul -Destination $destinationSoul -Force
}

foreach ($directory in @('inputs', 'drafts', 'qa', 'reports', 'templates')) {
    New-Item -ItemType Directory -Path (Join-Path $WorkspaceRoot $directory) -Force | Out-Null
}
Get-ChildItem -LiteralPath (Join-Path $repoRoot 'templates') -File |
    Copy-Item -Destination (Join-Path $WorkspaceRoot 'templates') -Force

foreach ($profile in $profiles) {
    Invoke-Hermes -Arguments @('-p', $profile.Name, 'config', 'set', 'terminal.backend', 'local')
    Invoke-Hermes -Arguments @('-p', $profile.Name, 'config', 'set', 'terminal.cwd', $WorkspaceRoot)
}

& (Join-Path $PSScriptRoot 'validate-repo.ps1')

Write-Host ''
Write-Host 'MiniCISO restaurado. Execute scripts\smoke-test.ps1 para validar o runtime.' -ForegroundColor Green

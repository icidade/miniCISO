[CmdletBinding()]
param(
    [string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }),
    [string]$WorkspaceRoot = $(Join-Path $HOME 'miniciso-security'),
    [switch]$SkipHermesInstall,
    [switch]$SkipProviderSetup,
    [switch]$ForceHermesReinstall
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$versionFile = Join-Path $repoRoot 'config\hermes-version.env'
$env:HERMES_HOME = $HermesHome

function Read-VersionFile([string]$Path) {
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match '^([A-Z0-9_]+)=(.+)$') { $values[$matches[1]] = $matches[2].Trim() }
    }
    return $values
}

function Canonical-Repo([string]$Value) {
    $trimmed = $Value -replace '\.git$', ''
    if ($trimmed -match '^https://github\.com/([^/]+)/([^/]+)$') { return "$($matches[1])/$($matches[2])" }
    if ($trimmed -match '^git@github\.com:([^/]+)/([^/]+)$') { return "$($matches[1])/$($matches[2])" }
    throw 'Unsupported Hermes repository URL.'
}

function Fail-Provenance([string]$Reason) { throw "Hermes provenance check failed: $Reason" }

function Prepare-Checkout([string]$RuntimeDir, [string]$ExpectedRepo, [string]$ExpectedCommit) {
    $expectedOwnerRepo = Canonical-Repo $ExpectedRepo
    if (-not (Test-Path -LiteralPath (Join-Path $RuntimeDir '.git'))) {
        New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
        & git -C $RuntimeDir init -q
        & git -C $RuntimeDir remote add origin $ExpectedRepo
    }
    & git -C $RuntimeDir rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { Fail-Provenance 'checkout is not a Git repository' }
    $origin = (& git -C $RuntimeDir config --get remote.origin.url 2>$null).Trim()
    if (-not $origin -or (Canonical-Repo $origin) -ne $expectedOwnerRepo) { Fail-Provenance 'origin does not match configured repository' }
    & git -C $RuntimeDir cat-file -e "$ExpectedCommit^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) { & git -C $RuntimeDir fetch --no-tags --depth=1 origin $ExpectedCommit }
    & git -C $RuntimeDir checkout --detach $ExpectedCommit | Out-Null
}

function Verify-Provenance([string]$RuntimeDir, [string]$ExpectedRepo, [string]$ExpectedCommit) {
    $expectedOwnerRepo = Canonical-Repo $ExpectedRepo
    & git -C $RuntimeDir rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { Fail-Provenance 'checkout is not a Git repository' }
    $head = (& git -C $RuntimeDir rev-parse HEAD).Trim()
    if ($head -ne $ExpectedCommit) { Fail-Provenance 'HEAD does not match configured commit' }
    $origin = (& git -C $RuntimeDir config --get remote.origin.url).Trim()
    if ((Canonical-Repo $origin) -ne $expectedOwnerRepo) { Fail-Provenance 'origin does not match configured repository' }
    $hermes = Join-Path $RuntimeDir 'venv\Scripts\hermes.exe'
    $python = Join-Path $RuntimeDir 'venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $hermes -PathType Leaf)) { Fail-Provenance 'Hermes executable is outside the governed checkout or missing' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { Fail-Provenance 'Hermes Python is outside the governed checkout or missing' }
    $probe = 'import importlib,pathlib,sys; runtime=pathlib.Path(sys.argv[1]).resolve(); names=("hermes_cli","hermes_cli.config","hermes_constants"); [(_ for _ in ()).throw(SystemExit("Hermes module outside governed checkout: "+n)) for n in names if runtime not in pathlib.Path(importlib.import_module(n).__file__).resolve().parents]; [(_ for _ in ()).throw(SystemExit("Hermes sys.path selects another checkout")) for p in sys.path if "hermes-agent" in p and pathlib.Path(p).resolve()!=runtime and runtime not in pathlib.Path(p).resolve().parents]'
    & $python -c $probe $RuntimeDir
    if ($LASTEXITCODE -ne 0) { Fail-Provenance 'Python modules or sys.path are outside the governed checkout' }
}

function Invoke-Hermes([string[]]$Arguments) {
    & $script:HermesCommand @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Hermes command failed: $($Arguments -join ' ')" }
}

$version = Read-VersionFile $versionFile
foreach ($key in @('HERMES_REPOSITORY', 'HERMES_COMMIT', 'HERMES_INSTALL_PS1_SHA256')) {
    if (-not $version.ContainsKey($key)) { throw "Missing key in hermes-version.env: $key" }
}
$runtimeDir = Join-Path $HermesHome 'hermes-agent'
$pythonCommand = (Get-Command python3, python, py -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $pythonCommand) { throw 'python3/python/py not found.' }

if ($ForceHermesReinstall -and (Test-Path -LiteralPath $runtimeDir)) { Remove-Item -LiteralPath $runtimeDir -Recurse -Force }
if (-not $SkipHermesInstall) {
    $trimmed = $version.HERMES_REPOSITORY -replace '\.git$', ''
    if ($trimmed -notmatch '^https://github\.com/([^/]+)/([^/]+)$') { throw 'Unsupported Hermes repository URL.' }
    $installerUri = "https://raw.githubusercontent.com/$($matches[1])/$($matches[2])/$($version.HERMES_COMMIT)/scripts/install.ps1"
    $installerPath = Join-Path ([IO.Path]::GetTempPath()) "hermes-install-$($version.HERMES_COMMIT).ps1"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $installerUri -OutFile $installerPath
        if ((Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash -ne $version.HERMES_INSTALL_PS1_SHA256) { throw 'Invalid Hermes installer checksum.' }
        Prepare-Checkout $runtimeDir $version.HERMES_REPOSITORY $version.HERMES_COMMIT
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath -Commit $version.HERMES_COMMIT -ForceCommit -HermesHome $HermesHome -InstallDir $runtimeDir -SkipSetup -NonInteractive
        if ($LASTEXITCODE -ne 0) { throw 'Hermes installer failed.' }
    } finally { Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue }
}

Verify-Provenance $runtimeDir $version.HERMES_REPOSITORY $version.HERMES_COMMIT
$script:HermesCommand = Join-Path $runtimeDir 'venv\Scripts\hermes.exe'
if (-not $SkipProviderSetup) { Invoke-Hermes @('setup') }

$profileRoot = Join-Path $HermesHome 'profiles'
$profiles = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'profiles') -Directory | Sort-Object Name)
if ($profiles.Count -ne 9) { throw "Expected 9 profiles; found $($profiles.Count)." }
foreach ($profile in $profiles) {
    $destinationDir = Join-Path $profileRoot $profile.Name
    if (-not (Test-Path -LiteralPath $destinationDir)) { Invoke-Hermes @('profile', 'create', $profile.Name, '--clone') }
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    $sourceSoul = Join-Path $profile.FullName 'SOUL.md'
    $destinationSoul = Join-Path $destinationDir 'SOUL.md'
    if ((Test-Path -LiteralPath $destinationSoul) -and ((Get-FileHash $sourceSoul).Hash -ne (Get-FileHash $destinationSoul).Hash)) { Copy-Item $destinationSoul "$destinationSoul.pre-miniciso" -Force }
    Copy-Item $sourceSoul $destinationSoul -Force
}

$chiefSkillsRoot = Join-Path $profileRoot 'chief-of-staff\skills'
Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills') -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring((Join-Path $repoRoot 'skills').Length + 1)
    $destination = Join-Path $chiefSkillsRoot $relative
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
    Copy-Item $_.FullName $destination -Force
}
& $pythonCommand (Join-Path $repoRoot 'scripts\install_governance_config.py') --source (Join-Path $repoRoot 'config\chief-of-staff.public.yaml') --profile-config (Join-Path $profileRoot 'chief-of-staff\config.yaml')
if ($LASTEXITCODE -ne 0) { throw 'Governance configuration installation failed.' }

foreach ($directory in @('inputs', 'drafts', 'qa', 'reports', 'templates')) { New-Item -ItemType Directory -Path (Join-Path $WorkspaceRoot $directory) -Force | Out-Null }
Get-ChildItem -LiteralPath (Join-Path $repoRoot 'templates') -File | Copy-Item -Destination (Join-Path $WorkspaceRoot 'templates') -Force
foreach ($profile in $profiles) { Invoke-Hermes @('-p', $profile.Name, 'config', 'set', 'terminal.backend', 'local'); Invoke-Hermes @('-p', $profile.Name, 'config', 'set', 'terminal.cwd', $WorkspaceRoot) }
& (Join-Path $PSScriptRoot 'validate-repo.ps1')
Write-Host 'MiniCISO restored. Run scripts\smoke-test.ps1 to validate the runtime.'
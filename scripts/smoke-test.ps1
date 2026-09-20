[CmdletBinding()]
param(
    [switch]$Online,
    [string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' })
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:HERMES_HOME = $HermesHome
$version = @{}
foreach ($line in Get-Content (Join-Path $repoRoot 'config\hermes-version.env')) { if ($line -match '^([A-Z0-9_]+)=(.+)$') { $version[$matches[1]] = $matches[2] } }
function Canonical-Repo([string]$Value) { $v = $Value -replace '\.git$', ''; if ($v -match '^https://github\.com/([^/]+)/([^/]+)$') { return "$($matches[1])/$($matches[2])" }; if ($v -match '^git@github\.com:([^/]+)/([^/]+)$') { return "$($matches[1])/$($matches[2])" }; throw 'Unsupported Hermes repository URL.' }
if ($version.HERMES_REPOSITORY -ne 'https://github.com/icidade/hermes-agent.git') { throw 'Unexpected Hermes repository.' }
if ($version.HERMES_COMMIT -ne 'a921e389f130b3a46c9f1b7363dae6ab1c87f6c5') { throw 'Unexpected Hermes commit.' }
$runtime = Join-Path $HermesHome 'hermes-agent'
$head = (& git -C $runtime rev-parse HEAD).Trim()
if ($head -ne $version.HERMES_COMMIT) { throw 'Hermes HEAD mismatch.' }
$origin = (& git -C $runtime config --get remote.origin.url).Trim()
if ((Canonical-Repo $origin) -ne (Canonical-Repo $version.HERMES_REPOSITORY)) { throw 'Hermes origin mismatch.' }
$hermes = Join-Path $runtime 'venv\Scripts\hermes.exe'
$python = Join-Path $runtime 'venv\Scripts\python.exe'
if (-not (Test-Path $hermes -PathType Leaf) -or -not (Test-Path $python -PathType Leaf)) { throw 'Hermes executable or Python missing from checkout.' }
$profiles = @(Get-ChildItem (Join-Path $repoRoot 'profiles') -Directory | Sort-Object Name | ForEach-Object Name)
$installed = @(& $hermes profile list | ForEach-Object { ($_ -split '\s+')[0] } | Where-Object { $_ } | Sort-Object -Unique)
if ((Compare-Object $profiles $installed)) { throw 'Hermes profiles do not match exactly.' }
foreach ($profile in $profiles) { $root = Join-Path $HermesHome "profiles\$profile"; if (-not (Test-Path (Join-Path $root 'SOUL.md')) -or -not (Test-Path (Join-Path $root 'config.yaml'))) { throw "Profile files missing: $profile" } }
$chief = Join-Path $HermesHome 'profiles\chief-of-staff'
if (-not (Test-Path (Join-Path $chief 'skills\cost-context-governance\SKILL.md'))) { throw 'Governance skill missing.' }
if (-not (Select-String (Join-Path $chief 'SOUL.md') 'cost-context-governance' -Quiet)) { throw 'Chief SOUL missing governance reference.' }
if (-not (Select-String (Join-Path $chief 'config.yaml') 'mode: enforce' -Quiet)) { throw 'Chief governance mode is not enforce.' }
if ($Online) { foreach ($profile in $profiles) { & $hermes -p $profile chat -Q -q 'Answer in one line starting with OK.' } }
Write-Host "Smoke test completed for $($profiles.Count) exact profiles."
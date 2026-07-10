# Installation and restoration

## Prerequisites

- Git
- HTTPS access to GitHub and the endpoints used by the official Hermes installer
- a valid credential for at least one Hermes-supported provider/model

Python, `uv`, Node.js, and the remaining runtime dependencies are managed by the official installer pinned by the project.

## Clean installation

Windows:

```powershell
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
.\scripts\bootstrap.ps1
```

Linux, macOS, or WSL2:

```bash
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
./scripts/bootstrap.sh
```

Provider setup is interactive because credentials do not belong in Git. To prepare only files/profiles in an already configured environment, use `-SkipProviderSetup` in PowerShell or `--skip-provider-setup` in Bash.

## What is reproducible

- Hermes upstream tag and commit
- upstream installer checksums
- profile names and prompts
- workspace structure
- terminal backend and working directory
- structural tests and smoke tests

Credentials, tokens, sessions, memories, and reports are local state intentionally not reproduced by the repository.

## Updating the overlay

```bash
git pull --ff-only
./scripts/bootstrap.sh --skip-hermes-install --skip-provider-setup
```

On Windows:

```powershell
git pull --ff-only
.\scripts\bootstrap.ps1 -SkipHermesInstall -SkipProviderSetup
```

The bootstrap creates a `.pre-miniciso` copy before replacing an existing different `SOUL.md`.

## Updating Hermes

Do not use a floating branch. Update `config/hermes-version.env` with an official release, its resolved commit, and the hashes of both installers. Then run the validations and test a clean restoration.

## Rollback

1. check out a previous commit from this repo;
2. run bootstrap again;
3. restore any `SOUL.md.pre-miniciso` only if you want to stop using the overlay-managed prompt.

## Verification

```powershell
.\scripts\validate-repo.ps1
.\scripts\smoke-test.ps1
```

```bash
./scripts/validate-repo.sh
./scripts/smoke-test.sh
```

The online smoke test is optional and requires credentials: `.\scripts\smoke-test.ps1 -Online` or `./scripts/smoke-test.sh --online`.

## Limitations

- The PDF catalog is a documentation artifact and is not part of runtime execution.
- External tools listed in `config/tooling-dependencies.example.yaml` are optional.
- The local backend gives profiles access to the host; use Docker/SSH/Singularity if your threat model requires isolation.

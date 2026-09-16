# Installation and restoration

## Prerequisites

- Git
- HTTPS access to GitHub and the endpoints used by the pinned Hermes fork installer
- a valid credential for at least one Hermes-supported provider/model

Python, `uv`, Node.js, and the remaining runtime dependencies are managed by the installer from the pinned fork commit.

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

- Hermes fork repository and exact commit
- fork installer checksums
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

Do not use a floating branch. Update `config/hermes-version.env` with a known Hermes fork repository, exact commit, and the hashes of both installers. The fork preserves its upstream relationship but is the canonical source for this overlay release.

## Rollback

1. choose a previously known-good Hermes SHA in `config/hermes-version.env`;
2. run bootstrap again with that pin;
3. restore any `SOUL.md.pre-miniciso` only if you want to stop using the overlay-managed prompt.

Rollback does not use a floating branch or destructive `git reset`/`git clean` operation.

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

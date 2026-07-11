# miniCISO

Agentic security staff for [Hermes Agent](https://github.com/NousResearch/hermes-agent), distributed as a reproducible overlay of profiles, prompts, templates, and operating policies.

> This repository is **not a Hermes fork**. The runtime is installed by the bootstrap from an immutable version and commit declared in [`config/hermes-version.env`](config/hermes-version.env).

## Quick restore

### Windows (PowerShell)

```powershell
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
.\scripts\bootstrap.ps1
```

### Linux, macOS, or WSL2

```bash
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
./scripts/bootstrap.sh
```

The bootstrap:

1. downloads the official Hermes installer from the pinned commit and validates its SHA-256;
2. installs the runtime without writing secrets into the repository;
3. runs local provider/model setup;
4. creates the nine MiniCISO profiles from the local configuration;
5. installs each `SOUL.md`, creates the shared workspace, and configures the local terminal;
6. runs structural checks.

Credentials requested by `hermes setup` remain in the user's Hermes environment. They are never copied into this repository.

## Profiles

- `chief-of-staff`: MiniCISO coordinator and final synthesis
- `security-threat-modeling`
- `security-architecture`
- `security-code-review`
- `security-appsec-assessment`
- `security-compliance-mapper`
- `security-offensive-security`
- `security-recon-attack-surface-strategist`
- `security-qa`: final quality gate

`chief-of-staff` is a dedicated Hermes profile fully managed by this overlay. The bootstrap does not modify the default Hermes profile prompt.

## Validation

Offline tree validation:

```powershell
.\scripts\validate-repo.ps1
```

```bash
./scripts/validate-repo.sh
```

After bootstrap, validate the runtime:

```powershell
.\scripts\smoke-test.ps1
```

Use `-Online`/`--online` to also send a short question to each profile. That mode consumes the configured provider.

## Security and privacy

The repo contains only non-secret configuration and sanitized content. Do not publish `.env`, tokens, sessions, memories, logs, or real reports. See [`SECURITY.md`](SECURITY.md) and [`.env.example`](.env.example).

## Safe overlay self-update

The repo can now maintain a public, sanitized copy of what is running on the VPS without publishing private state.

Key additional public artifacts:

- `tools/headroom_phase1/`: indexer, KAG query builder, selector, and Headroom Phase 1.1A wrapper
- `config/chief-of-staff.public.yaml`: sanitized snapshot of the main profile's non-secret configuration
- `scripts/export_safe_self_state.py`: safe export of public state into the repo

Quick flow:

```bash
python3 scripts/export_safe_self_state.py --apply
./scripts/validate-repo.sh
```

## External finding workflow

For bug bounty / external vulnerability work:

- no external report draft should start before a `GO` decision;
- `RESEARCH` means produce a safe impact-validation plan, not a submission draft;
- `NO-GO` means block submission and register the lesson learned.

See [`docs/kag-finding-validation.md`](docs/kag-finding-validation.md), [`templates/finding-decision-template.md`](templates/finding-decision-template.md), [`docs/submission-followup.md`](docs/submission-followup.md), and [`templates/submission-followup-template.md`](templates/submission-followup-template.md).

## Documentation

- [`INSTALL.md`](INSTALL.md): installation, updates, rollback, and limitations
- [`docs/staff-operating-model.md`](docs/staff-operating-model.md): operating flow
- [`docs/profile-setup.md`](docs/profile-setup.md): profile contract
- [`docs/dependencies-and-configuration.md`](docs/dependencies-and-configuration.md): optional dependencies
- [`docs/headroom-kag-selective-retrieval.md`](docs/headroom-kag-selective-retrieval.md): public architecture for the Headroom + KAG track
- [`docs/kag-finding-validation.md`](docs/kag-finding-validation.md): pre-submission KAG gate for finding validation
- [`docs/submission-followup.md`](docs/submission-followup.md): post-submission follow-up tracking and triage-response workflow
- [`docs/self-update-capability.md`](docs/self-update-capability.md): public export/sync capability
- [`docs/github-pr-access.md`](docs/github-pr-access.md): minimal PAT and credential setup on the VPS
- [`miniciso-staff-service-catalog-v5.md`](miniciso-staff-service-catalog-v5.md): service catalog source
- [`miniciso-staff-service-catalog-v5-full.pdf`](miniciso-staff-service-catalog-v5-full.pdf): service catalog PDF

## License

[MIT](LICENSE). Hermes Agent is a separate project and keeps its own license.

# Repo Architecture Recommendation

## Preferred model

Use **Hermes as an upstream dependency** and keep MiniCISO as a separate public, sanitized overlay repository.

That means:
- Hermes core stays updateable with low friction.
- MiniCISO prompts, profiles, templates, and docs remain your own product layer.
- A fork of Hermes becomes necessary only if you must patch Hermes core behavior.

## Recommended repository structure

```text
hermes-miniciso/
  README.md
  INSTALL.md
  docs/
    staff-operating-model.md
    profile-setup.md
    repo-architecture.md
    repo-mapping.md
    dependencies-and-configuration.md
  chief-of-staff/
    SOUL-miniciso-snippet.md
  profiles/
    chief-of-staff/SOUL.md
    security-threat-modeling/SOUL.md
    security-architecture/SOUL.md
    security-code-review/SOUL.md
    security-appsec-assessment/SOUL.md
    security-compliance-mapper/SOUL.md
    security-offensive-security/SOUL.md
    security-recon-attack-surface-strategist/SOUL.md
    security-qa/SOUL.md
  templates/
    intake-template.md
    report-template.md
  scripts/
    bootstrap.ps1
    bootstrap.sh
    smoke-test.ps1
    smoke-test.sh
    validate-repo.ps1
    validate-repo.sh
    sync_to_hermes.sh
  config/
    hermes-version.env
    tooling-dependencies.example.yaml
  meta/
    MANIFEST.json
    SUMMARY.json
```

## Separation of concerns

### Keep in this repo
- operating model
- prompts and `SOUL.md`
- staff definitions
- templates
- helper scripts
- dependency documentation
- optional examples and QA patterns

### Keep out of this repo
- live credentials
- live environment secret files and auth state
- session history
- logs
- memories
- report outputs with sensitive content unless explicitly sanitized

## When to keep Hermes only as dependency
Choose dependency-only when you are changing:
- prompts
- workflow
- profile layout
- templates
- security operating model
- documentation
- helper scripts

## When to create or maintain a Hermes fork
Choose fork only when you need to change:
- Hermes CLI behavior
- gateway adapters
- scheduler/runtime behavior
- tool registration or tool semantics
- prompt builder internals
- profile lifecycle inside Hermes core

## Promotion path
1. Author and review content in this repo.
2. Pin an official Hermes release and commit in `config/hermes-version.env`.
3. Restore with the platform bootstrap, which creates dedicated named profiles.
4. Validate with the offline validator and runtime smoke test.
5. Promote to daily use only after review of the local provider and isolation settings.

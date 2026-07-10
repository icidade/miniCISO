# Self-update capability (public/safe overlay)

This capability exists to keep the public `miniCISO` repository aligned with the live VPS instance **without copying private state**.

## Goal

Generate a public and safe copy of:

- local Headroom/KAG tools that make sense as public overlay assets;
- a sanitized snapshot of the `chief-of-staff` profile's non-secret configuration;
- non-confidential methodology documentation.

## What is included

The current safe export covers:

- `tools/headroom_phase1/*.py`
- `tools/headroom_phase1/tests/test_*.py`
- `config/chief-of-staff.public.yaml`

## What stays out

Never export:

- `.env`, `.env.*`, tokens, PATs, API keys
- `auth.json`, `hosts.yml`, cookies, `gh` credentials
- memories, sessions, logs, cron output
- raw assessment artifacts
- references to specific active BBP programs
- findings, triage notes, or sensitive evidence

## Export script

The current export is **allowlisted + scanned + reviewed-by-diff**:

- it copies only a fixed set of public Headroom/KAG files;
- it blocks if suspicious secret or operational-state patterns are detected;
- it still requires human review of `git diff` before commit/push.

Use:

```bash
python3 scripts/export_safe_self_state.py
```

Apply mode:

```bash
python3 scripts/export_safe_self_state.py --apply
```

You can also point to explicit sources:

```bash
python3 scripts/export_safe_self_state.py \
  --source-workspace /home/vpsadmin/miniciso-security \
  --source-profile /home/vpsadmin/.hermes/profiles/chief-of-staff \
  --apply
```

## Recommended update flow

1. Run the safe export.
2. Review `git diff` in the public repo.
3. Run `./scripts/validate-repo.sh`.
4. Run public tool tests when applicable.
5. Commit on a dedicated branch.
6. Open a PR.

## Inclusion criteria

Before promoting something from the live runtime into the public repo, confirm that it:

- is reproducible;
- is generally useful;
- does not reveal secrets or private context;
- does not depend on a specific active program/engagement;
- still makes sense outside the current VPS.

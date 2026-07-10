# Repo Mapping

This repository is the canonical public MiniCISO overlay. It is consumed directly; it is not copied into a Hermes fork.

## Source-to-runtime mapping

```text
profiles/<profile>/SOUL.md
  -> ~/.hermes/profiles/<profile>/SOUL.md

templates/*
  -> ~/miniciso-security/templates/*

config/hermes-version.env
  -> immutable input for the official Hermes installer
```

The `inputs`, `drafts`, `qa`, `reports`, and `templates` directories are created under `~/miniciso-security` (or the path configured in bootstrap).

## Chief of staff

`chief-of-staff` is a dedicated named profile, not the default Hermes profile. For that reason, its full `SOUL.md` is managed by the overlay. The snippet in `chief-of-staff/` remains only as a reference for users who prefer manual integration.

## Public runtime exports

```text
tools/headroom_phase1/*
  -> repo-side public operator tooling (not auto-synced into Hermes home)

config/chief-of-staff.public.yaml
  -> sanitized reference snapshot of non-secret live configuration
```

Use `scripts/export_safe_self_state.py --apply` to refresh those artifacts from the VPS, always with manual diff review before commit/push.

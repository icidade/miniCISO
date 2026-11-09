# Governance recovery and operations

## Root cause

The approval incident was not an identity or stable-ID failure. The same
profile, engagement, task, logical call, and owner remained bound throughout.
The approved per-request envelope was 37,197 tokens; the next resume message
was estimated at 37,352 tokens. The old runtime raised a generic persistence
exception because the resume exceeded the exact approved cap by 155 tokens.
The authorization therefore remained approved but could not be consumed, and
the operator received no actionable explanation.

Context growth amplified the incident. The affected conversation had reached
34,263 input tokens before the block, the next estimate was 37,197, and the
serialized tool schema was about 30 KB even though only two of twenty exposed
tools were used. A duplicate governance-skill installation also caused failed
skill lookups. These are operational contributors, not reasons to weaken the
security boundary.

## Control design

- `log` records decisions and artifacts without blocking solely on consumption
  budget; `block` enforces the same boundaries. `observe` and `enforce` are
  legacy aliases.
- The approval envelope shown to the owner includes deterministic resume
  headroom: the greater of 1,024 tokens or 5% by default.
- The persisted authorization lifecycle is `requested → approved → reserved →
  resumed → consumed`. A pre-provider release returns it to `approved`.
- Authenticated callback retries are idempotent and remain bound to the stable
  profile, engagement, task, platform, chat, and subject.
- `!governance status`, `!governance mode log`, and `!governance mode block`
  are intercepted before session/model work. Only stable IDs in the active
  profile's explicit per-platform administrator allowlist are accepted.
- Chat administration cannot disable governance. Local operators retain the
  budget-independent `python -m agent.governance_admin` path.

## Rollout

1. Back up the active profile config and capture the current runtime SHA and
   service status.
2. Deploy the immutable Hermes SHA in `config/hermes-version.env`.
3. Configure the active profile in `log` mode and add only the required stable
   platform administrator IDs. Never publish those IDs in this repository.
4. Restart every service sharing the Hermes checkout.
5. Validate runtime provenance, service health, log-mode non-blocking behavior,
   unauthorized-command denial, authorized status/mode routing, approval
   lifecycle, release/retry, and multiprocess locking.
6. Promote to `block` only after reviewing telemetry and context/tool exposure.

Rollback is configuration-first: use the authenticated command or local CLI to
return to `log`. If code rollback is required, restore the previous immutable
Hermes SHA and the backed-up config, then restart all services sharing the
checkout. Do not edit persisted authorization or accounting records by hand.

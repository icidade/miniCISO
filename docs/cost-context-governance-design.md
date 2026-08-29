# Cost & Context Governance — v0.7.0 Phase 1 Design

## Version
This document captures the MiniCISO-side design and documentation updates aligned to the Hermes cost/context governance v0.7.0 rollout.

## Goal
Implement a mandatory, provider-independent governance layer for MiniCISO that preserves evidence quality and independent QA while preventing runaway token/context/tool consumption.

## Repositories inspected
- MiniCISO overlay checkout: `<miniCISO-repo-root>`
- Hermes runtime checkout: `<hermes-agent-repo-root>`

## Existing integration points

### MiniCISO overlay
- `profiles/chief-of-staff/SOUL.md`: core Chief-of-Staff operating instructions. Best place to make the governance skill mandatory at the procedural layer.
- `config/chief-of-staff.public.yaml`: public example config that can expose governance defaults.
- No existing MiniCISO-owned runtime package for deterministic governance.

### Hermes runtime
- `run_agent.py`: `AIAgent` wrappers, turn execution entrypoints, tool execution dispatch, `delegate_task` dispatch, context compression hook.
- `agent/conversation_loop.py`: main model-call loop, iteration handling, context growth, turn completion path.
- `agent/context_compressor.py`: existing compaction/externalization mechanism.
- `agent/tool_executor.py`: deterministic tool execution path; best insertion point for tool-call accounting and pre-tool circuit breakers.
- `agent/tool_guardrails.py`: existing repeated-tool/no-progress primitive that can be complemented by broader engagement governance.
- `tools/delegate_tool.py`: child-agent creation, task context packaging, timeout/error/summary handling; best insertion point for child budget allocation, bounded child context manifests, and structured partial handoffs.
- `model_tools.py`: tool-definition assembly; best insertion point for exact allowlist filtering and tool-schema overhead measurement.
- `hermes_cli/config.py`: default config surface for observe/enforce/disabled modes and budget profiles.

## Selected implementation strategy
Use a dual-layer design:

1. **Procedural layer (MiniCISO-owned)**
   - Add mandatory skill `cost-context-governance`.
   - Patch Chief-of-Staff SOUL to require loading/classification on every request.
   - Keep conversational requests lightweight via explicit pass-through classification.

2. **Runtime layer (Hermes-side generic enforcement, MiniCISO-enabled by config)**
   - Add a new controller module that:
     - classifies requests;
     - creates an engagement workspace + JSON artifacts;
     - allocates hierarchical envelopes;
     - records telemetry/context manifests/tool-schema overhead;
     - enforces model/tool/delegation/time/context thresholds;
     - preserves partial handoffs on timeout/hard stop.
   - Enable by default in the active Chief-of-Staff profile config.

## Affected files

### New files
- `<hermes-agent-repo-root>/agent/cost_context_governance.py`
- `<hermes-agent-repo-root>/tests/agent/test_cost_context_governance.py`
- `<hermes-agent-repo-root>/tests/tools/test_delegate.py`
- `skills/cost-context-governance/SKILL.md`
- `docs/cost-context-governance-design.md`

### Patched Hermes files
- `run_agent.py`
- `agent/conversation_loop.py`
- `agent/tool_executor.py`
- `tools/delegate_tool.py`
- `model_tools.py`
- `hermes_cli/config.py`

### Patched MiniCISO/profile files
- `profiles/chief-of-staff/SOUL.md`
- `<hermes-profile-root>/SOUL.md`
- `<hermes-profile-root>/config.yaml`
- `<hermes-profile-root>/skills/cost-context-governance/SKILL.md`

## Runtime data layout
Under the active profile:
- `engagements/<engagement_id>/brief.json`
- `engagements/<engagement_id>/budget.json`
- `engagements/<engagement_id>/telemetry.jsonl`
- `engagements/<engagement_id>/evidence_ledger.jsonl`
- `engagements/<engagement_id>/claim_ledger.jsonl`
- `engagements/<engagement_id>/checkpoints/*.json`
- `engagements/<engagement_id>/partial_handoffs/*.json`

## Scope of first implementation
Implemented now for immediate VPS effect:
- observe/enforce/disabled modes;
- root + child envelope accounting with file-lock persistence;
- configurable budget profiles and QA reserve;
- model/tool/delegation/time/context thresholds;
- context manifests and tool-schema overhead metrics;
- bounded child context package metadata;
- structured partial handoffs on timeout / limit / hard stop;
- role/toolset filtering via runtime allowlist intersection;
- local JSONL telemetry and engagement summaries.

## Compatibility risks
- Hermes currently lacks a native pre-model-call governance abstraction, so the first implementation must patch runtime call sites directly.
- Tool filtering must not break existing sessions that intentionally grant broader toolsets; fallback is intersection-only when governance is active.
- Child timeout handling varies by provider/runtime path; partial handoff synthesis must work even when the provider returns no summary.
- Existing MiniCISO repo has no skill-sync convention yet; immediate VPS install will patch the active profile directly and also stage the skill inside the overlay repo.

## Test plan
Automated tests will cover at least:
- threshold/circuit-breaker evaluation before 50 unbounded child calls;
- concurrency-safe shared root budget;
- timeout → persisted partial handoff (not null);
- QA reserve protection;
- per-task tool filtering before schema assembly;
- measurable unused tool-schema overhead;
- compaction/externalization before threshold breach;
- lightweight conversational pass-through;
- usage estimation fallback when provider metadata is missing.

## Why MiniCISO-level enforcement alone is insufficient
MiniCISO prompt/skill instructions can require planning and checkpointing, but they cannot deterministically:
- prevent an agent from sending oversized tool schemas;
- stop a child before the next model call once budget is exhausted;
- atomically coordinate concurrent child consumption from a shared root budget;
- force structured partial handoffs when runtime timeouts occur.

Therefore the smallest required upstream-compatible change is a generic Hermes runtime governance controller that MiniCISO enables by config. The fallback for unsupported runtimes is visible observation-only mode with explicit warning in child/task results.

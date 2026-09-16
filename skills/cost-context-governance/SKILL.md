---
name: cost-context-governance
description: Mandatory execution governance for Chief-of-Staff and MiniCISO work. Classifies every request, plans bounded resource use, preserves QA reserve, constrains delegation/tool schemas, and persists resumable partial handoffs.
version: 0.7.0
author: MiniCISO
license: MIT
metadata:
  miniciso:
    mandatory_for_profiles:
      - chief-of-staff
    request_classes:
      - conversational
      - bounded
      - engagement
    separates_from:
      - KAG
      - Headroom
      - Institutional Learning
      - Security QA
---

# Cost & Context Governance

## Purpose

This skill is mandatory for the `chief-of-staff` profile on **every** request.

It keeps simple conversation lightweight while forcing bounded planning and resumable execution for work that can otherwise explode in cost, context size, delegation fan-out, or runtime.

## Required classification on every request

Before deep execution, classify the request as exactly one of:

1. `conversational`
2. `bounded`
3. `engagement`

### Classification guidance

- `conversational`: normal chat, quick answer, light triage, no sustained tool loop expected.
- `bounded`: contained implementation, focused review, short investigation, or a task that needs tools/delegation but should stay within a small envelope.
- `engagement`: multi-step assessment, MiniCISO/security work, delegated multi-lane execution, long research, or anything requiring evidence/claim tracking and final QA.

For `conversational`, do the lightest possible governance pass and continue.

For `bounded` or `engagement`, governance must become explicit and visible.

## Mandatory operating sequence

### 1. Establish the execution shape

For `bounded` and `engagement` work, define before deep execution:

- objective
- scope
- exclusions
- chosen budget profile
- expected artifacts
- required roles/SMEs
- QA obligation
- checkpoint / handoff triggers

### 2. Create isolated state

Long-running work must not rely on the active chat as full working memory.

Use isolated task or engagement state and keep the conversational Chief session limited to:

- user intent
- scope and exclusions
- approvals
- key decisions
- concise progress
- resource state
- artifact references
- final summary

Do **not** continuously re-inject:

- raw SME transcripts
- full tool dumps
- complete engagement history
- prior report drafts in full
- every child conversation

### 3. Choose only necessary roles and tools

- select only the SMEs actually required by the task
- do not spawn all SMEs by default
- restrict tools by role and task
- send the smallest viable tool/schema surface
- give each child only the context package it needs

### 4. Preserve Security QA reserve

A protected QA reserve is mandatory for `bounded` and `engagement` work that will end in validation.

Rules:

- reserve budget before exploration starts
- do not let SME or synthesis work silently consume it
- if remaining headroom threatens QA viability, checkpoint and pause/escalate
- final user-facing security claims still require independent `security-qa`

### 5. Allocate bounded child envelopes

Delegated children must receive:

- a bounded child budget
- a bounded child context package
- only the required tools
- a resume identifier / handoff target

Children must **not** inherit the full root budget by default.

### 6. Monitor measurable progress

Track real progress through state change, not optimistic narration.

Examples of valid progress:

- evidence added
- claim created or updated
- claim supported / contradicted / rejected / closed
- open question resolved
- expected artifact produced
- required phase completed

Examples of non-progress that must count against the breaker:

- repeated equivalent tool calls
- repeated provider or tool failures
- repeated restatement of the same plan
- context growth with no evidence/claim delta
- retry loops without new information

### 7. Checkpoint before hard stops

Before likely timeout, budget exhaustion, no-progress break, or operator pause:

- checkpoint current state
- persist partial work
- externalize large context when needed
- leave artifact references, open questions, and recommended next step

Expensive work must never disappear into `null`.

### 8. Escalate intentionally

Request user approval when the work must:

- widen scope materially
- consume a larger budget profile
- add new external testing lanes
- spend protected reserve
- continue after a circuit breaker or hard stop

## Required closure summary

At the end of bounded or engagement work, summarize actual usage:

- request class
- selected profile
- model/tool/delegation usage
- checkpoints created
- handoffs created
- reserve status
- remaining limitations
- next recommended step

## Separation of concerns

Keep these layers distinct:

### KAG
Relevance and knowledge selection for the current question.

### Headroom
Selective retrieval and compression for large artifacts.

### Cost & Context Governance
Execution control, resource envelopes, context growth control, delegation control, progress breakers, checkpointing, and resumability.

### Institutional Learning
Prior operational judgment and lessons learned that tighten decisions.

### Security QA
Independent validation of claims, evidence quality, and closure readiness.

None of the other layers replace governance, and governance does not replace them.

## Minimum checklist for bounded/engagement work

- [ ] Request classified
- [ ] Budget profile chosen
- [ ] Isolated state established
- [ ] QA reserve protected
- [ ] Child budgets bounded
- [ ] Child context packages bounded
- [ ] Tool allowlist minimized
- [ ] Progress signals defined
- [ ] Checkpoint triggers defined
- [ ] Partial handoff format available
- [ ] Closure usage summary produced

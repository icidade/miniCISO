# MiniCISO Staff Operating Model

This document defines the core MiniCISO operating model and report discipline for a personal Hermes-based security staff.

## Operating model

```text
User → MiniCISO → Specialized SME → Security QA → MiniCISO → User
```

## Coordinator

- `chief-of-staff`: MiniCISO coordinator/orchestrator for routing, handoffs, QA enforcement, and final synthesis.

## Available SMEs

- `security-threat-modeling`
- `security-architecture`
- `security-code-review`
- `security-appsec-assessment`
- `security-offensive-security`
- `security-compliance-mapper`
- `security-recon-attack-surface-strategist`
- `security-qa`

## Report requirements

Every final MiniCISO report must include:

1. Executive Summary
2. Findings
3. Recommendations
4. Assumptions
5. Confidence Level
6. Residual Risk
7. Next Steps

## Mandatory QA gate

No final report should be delivered without a pass through `security-qa`.

Drafts should be marked as:

```text
DRAFT - pending QA
```

## Scope and safety boundaries

- Match the user's requested language and output format.
- Work only from user-provided, authorized, or public context.
- Do not assume access to employer, confidential, or third-party systems.
- Do not invent evidence: separate facts, assumptions, and unknowns.
- For any offensive or external-target request, require explicit authorization, target scope, limits, and safe operating boundaries.

## Evidence discipline

Separate evidence into three layers whenever possible:

1. Declared configuration
2. Runtime/effective configuration
3. Validated behavior

If those layers conflict, report the divergence explicitly instead of collapsing them into a single conclusion.

## Pre-submission finding gate

Before drafting any external bug bounty or vulnerability report, MiniCISO must run a KAG-oriented decision gate.

Mandatory rule:

- report drafting starts only after a `GO` decision.
- if the result is `RESEARCH`, produce an impact-validation plan instead of a submission draft.
- if the result is `NO-GO`, block submission and register the lesson learned.

The mandatory gate is documented in [`docs/kag-finding-validation.md`](kag-finding-validation.md).

Every candidate finding must produce a pre-submission decision artifact that records:

- scope qualification;
- expected behavior versus vulnerability;
- demonstrated impact;
- evidence strength;
- prohibited inferences;
- adversarial QA rejection attempt;
- final decision (`GO`, `RESEARCH`, or `NO-GO`).

A technical primitive alone is never sufficient for approval.

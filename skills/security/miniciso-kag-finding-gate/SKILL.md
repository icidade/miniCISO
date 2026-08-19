---
name: miniciso-kag-finding-gate
description: "Use when MiniCISO must decide whether an external security claim is ready for report drafting via the mandatory GO / RESEARCH / NO-GO gate."
version: 1.0.0
author: MiniCISO
license: MIT
metadata:
  hermes:
    tags: [miniciso, security, kag, finding-validation, bug-bounty, gate]
    related_skills: [miniciso-headroom-phase1, miniciso-institutional-learning]
---

# MiniCISO KAG Finding Gate

## Overview

This skill encodes the mandatory pre-submission decision gate for external findings, bug bounty drafts, and vulnerability claims.

Its purpose is to stop technical primitives, expected behavior, vague impact narratives, or scope confusion from becoming external reports without sufficient evidence. The output is a decision artifact with one of three states:

- `GO`
- `RESEARCH`
- `NO-GO`

This is a default MiniCISO behavior, not an optional style preference.

## When to Use

Use this skill when:

- drafting or reviewing an external vulnerability report;
- triaging a bug bounty candidate finding;
- deciding whether a discovered behavior is a vulnerability or expected product behavior;
- converting a technical observation into a claim with security consequences.

Do **not** skip this skill when:

- the user already believes the finding is valid;
- an SME sounds confident but evidence is still partial;
- the primitive looks familiar from prior cases.

## Mandatory Rule

Report drafting starts only after a `GO` decision.

- `GO` → report drafting may begin.
- `RESEARCH` → produce a safe impact-validation plan instead of a submission draft.
- `NO-GO` → block submission and register the lesson learned.

A technical primitive alone is never sufficient for approval.

## Required Inputs

Before running the gate, gather as much of the following as is available:

- target program and scope posture;
- asset or endpoint under test;
- finding class;
- primitive demonstrated;
- expected product behavior versus suspected vulnerability;
- security boundary allegedly crossed;
- evidence of attacker advantage and concrete consequence;
- applicable exclusions or program rules.

If required context is missing, the correct output is usually `RESEARCH` or `NO-GO`, not speculative approval.

## Decision Workflow

### 1. Qualify scope

Confirm whether the program, target, and behavior are in scope.

Questions:

- Is the asset in scope?
- Is the class of behavior in scope?
- Is there an exclusion that already blocks the claim?

### 2. Separate primitive from impact

Record the primitive precisely, then ask what unauthorized capability or security property violation was actually demonstrated.

Examples of dangerous inflation:

- misconfiguration → compromise;
- internal reference → SSRF impact;
- feature behavior → authz bypass;
- data exposure possibility → confirmed sensitive leak.

### 3. Check evidence strength

For each claim, classify the supporting basis:

- `DIRECT`
- `SUPPORTED_INFERENCE`
- `SPECULATIVE`
- `UNSUPPORTED`

`SPECULATIVE` or `UNSUPPORTED` claims cannot carry title, impact, or severity.

### 4. Attempt adversarial rejection

Before approving, construct the strongest legitimate rejection argument:

- expected behavior explanation;
- missing proof;
- exclusion-backed rejection;
- alternative benign interpretation.

If the rejection case still dominates, do not approve `GO`.

### 5. Produce the final decision

Use these defaults:

- choose `GO` only when impact is directly demonstrated and the rejection case is overcome;
- choose `RESEARCH` when a safe, authorized next test could close a real evidence gap;
- choose `NO-GO` when the issue is blocked by scope, exclusion, lack of qualifying impact, or a known bad inference.

## Required Artifact

Use `templates/finding-decision-template.md` and fill it before any external draft.

At minimum, the artifact must record:

- scope qualification;
- expected behavior versus vulnerability;
- demonstrated impact;
- evidence strength;
- prohibited inferences;
- adversarial QA rejection attempt;
- final decision and rationale;
- lesson learned / repeat error to avoid.

## Relationship to Other MiniCISO Defaults

- Pair with `miniciso-institutional-learning` when prior lessons learned reveal a known error pattern.
- Pair with `miniciso-headroom-phase1` when evidence comes from large structured artifacts that need selection-first retrieval.
- Every final report still passes through `security-qa` before delivery to the user.

## Common Pitfalls

1. **Approving based on class reputation.**
   A famous bug class does not replace current-case proof.

2. **Calling it `RESEARCH` when no new evidence path exists.**
   If the only remaining move is stronger rhetoric about the same primitive, prefer `NO-GO`.

3. **Ignoring exclusions because the behavior feels dangerous.**
   A blocked category is still blocked unless an allowed exception is independently demonstrated.

4. **Skipping the rejection attempt.**
   If the claim cannot survive its strongest fair rebuttal, it is not ready.

## Verification Checklist

- [ ] A finding-decision artifact exists for the candidate claim.
- [ ] Scope and exclusions were evaluated explicitly.
- [ ] Primitive and demonstrated impact were separated.
- [ ] Claims were labeled by evidence strength.
- [ ] Strongest rejection argument was recorded.
- [ ] Final decision is `GO`, `RESEARCH`, or `NO-GO` with rationale.
- [ ] If not `GO`, no external draft title is produced.
- [ ] `security-qa` remains the mandatory final delivery gate.

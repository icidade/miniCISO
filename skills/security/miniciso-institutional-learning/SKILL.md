---
name: miniciso-institutional-learning
description: "Use when MiniCISO should consult prior lessons learned to tighten reasoning, claims, confidence, or evidence thresholds without replacing current-case proof."
version: 1.0.0
author: MiniCISO
license: MIT
metadata:
  hermes:
    tags: [miniciso, security, institutional-learning, lessons-learned, qa]
    related_skills: [miniciso-kag-finding-gate, miniciso-headroom-phase1]
---

# MiniCISO Institutional Learning

## Overview

This skill turns lessons learned into an explicit MiniCISO reasoning discipline instead of leaving them as vague memory.

The capability exists to help the `chief-of-staff` and SMEs detect repeated methodological errors, tighten evidence thresholds, and reduce disagreement between draft outputs and `security-qa`. Prior experience is a guardrail and planning input; it is never substitute evidence.

## When to Use

Use this skill when:

- the current case resembles a prior false positive, rejected report, or QA correction;
- a reasoning path feels familiar and might be repeating an earlier analytical mistake;
- the task involves external finding validation, confidence calibration, or overclaim risk;
- a final `NO-GO` or strong QA correction should become a reusable methodological rule.

Do **not** use prior lessons to:

- claim current-case impact without fresh proof;
- override scope rules;
- increase severity by analogy alone;
- bypass the KAG gate or the `security-qa` gate.

## Core Principle

Lessons learned are decision support, not substitute evidence.

They may:

- shape the analysis plan;
- warn about known failure modes;
- tighten claim language;
- raise the evidence threshold for `GO`;
- force explicit prohibited-inference tracking.

They must not:

- replace direct evidence from the current case;
- promote severity without fresh proof;
- convert precedent into a finding by itself.

## Retrieval Moments

### 1. Before analysis

Consult prior lessons when the initial problem framing resembles a known category of failure.

Typical examples:

- repeated bug bounty patterns;
- runtime-versus-declared configuration disputes;
- expected-feature-versus-vulnerability confusion;
- impact inflation from a technical primitive.

### 2. During analysis

Use prior lessons to test whether the current reasoning path is repeating a known mistake.

Questions to ask:

- Are we repeating a previously rejected inference?
- Are we treating declared state as effective state?
- Are we jumping from possibility to demonstrated consequence?
- Are we relying on anecdote where fresh evidence is required?

### 3. After analysis

When `NO-GO` or QA materially corrects the result, capture the methodological lesson so future work becomes more conservative and more consistent.

## Output Shape

When the capability is relevant, pair the main artifact with an `Institutional Retrieval` block that records:

- lessons consulted;
- applicability level;
- prohibited inference to avoid;
- effect on confidence, evidence threshold, or next step.

Use the optional companion described in `templates/finding-decision-template.md`.

## Decision Impact

Institutional learning can legitimately influence:

- confidence level;
- required evidence before `GO`;
- whether the next step is `RESEARCH` instead of report drafting;
- whether `NO-GO` should be recorded and explained;
- which repeat error to avoid must be named explicitly.

## Relationship to Other MiniCISO Defaults

- Use `miniciso-kag-finding-gate` for the mandatory GO / RESEARCH / NO-GO decision on external findings.
- Use `miniciso-headroom-phase1` when large artifacts need deterministic, selection-first retrieval.
- Final reports still require the `security-qa` pass before delivery.

## Common Pitfalls

1. **Treating precedent as proof.**
   Similarity to an earlier case can constrain reasoning, but cannot prove the present one.

2. **Remembering only the claim, not the failure mode.**
   The lesson should capture the analytical mistake or QA guardrail, not just the topic label.

3. **Using lessons learned only after QA rejects the draft.**
   The capability is strongest when used before and during analysis, not just as postmortem cleanup.

4. **Capturing lessons too vaguely.**
   "Be careful with auth bugs" is weak. "Do not infer tenant breakout from reflective IDOR behavior without demonstrated cross-tenant attacker advantage" is useful.

## Verification Checklist

- [ ] A relevant prior lesson was consulted when the case resembles a known failure mode.
- [ ] Prior precedent was not treated as direct proof.
- [ ] The effect on claims, confidence, threshold, or next step is explicit.
- [ ] If the result is `NO-GO` or materially corrected, a reusable lesson is captured.
- [ ] KAG and `security-qa` still govern final delivery decisions.

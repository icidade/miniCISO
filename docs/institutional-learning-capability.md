# Institutional Learning Capability

This document describes MiniCISO's ability to evaluate prior operational experience through lessons learned before, during, and after a security engagement.

## Objective

MiniCISO treats experience as a first-class reasoning input, not as informal memory.

The goal is to reduce:

- repeated methodological mistakes;
- overclaiming from technical primitives alone;
- weak analogy between unrelated cases;
- loss of operational context across engagements;
- avoidable disagreement between SME output and Security QA.

## Core principle

Lessons learned are decision support, not substitute evidence.

They may:

- shape the analysis plan;
- warn about prior failure modes;
- tighten claim language;
- raise required evidence thresholds;
- trigger QA guardrails.

They must not:

- replace direct evidence from the current case;
- promote severity without fresh proof;
- override scope rules or exclusions;
- convert a weak hypothesis into a valid finding by precedent alone.

## Where this capability applies

### 1. Before analysis

MiniCISO can retrieve relevant prior lessons before a deep assessment starts.

Typical use cases:

- external bug bounty triage;
- impact validation planning;
- repeated security review patterns;
- runtime-versus-declared configuration disputes;
- cases where a prior false positive or rejected report resembles the current one.

Expected effect:

- the primary SME begins with institutional guardrails instead of rediscovering them midstream.

### 2. During analysis

MiniCISO can use lessons learned to evaluate whether the current reasoning is repeating a known error pattern.

Examples:

- mistaking declared configuration for effective state;
- treating feature behavior as a vulnerability without boundary break;
- inferring impact from class reputation instead of observed consequence;
- escalating from possibility to demonstrated compromise.

Expected effect:

- claims are downgraded earlier when evidence is insufficient.

### 3. After analysis

When the final decision is `NO-GO`, blocked, or materially corrected by QA, MiniCISO can register a new lesson learned so the same mistake becomes harder to repeat.

Expected effect:

- the operating model improves over time instead of only producing isolated outputs.

## Minimum retrieval dimensions

When institutional retrieval is used, MiniCISO should query prior experience across at least some of these dimensions:

- technical domain;
- finding class;
- trust boundary type;
- evidence failure mode;
- program policy or exclusion pattern;
- QA rejection pattern;
- operational workflow failure;
- report-language overclaim pattern.

## Expected output shape

A working artifact or report can include an `Institutional Retrieval` block such as:

```yaml
Institutional Retrieval:
  status: lessons_found | lessons_not_found | lessons_found_but_low_applicability
  lessons_consulted:
    - id:
      title:
      applicability: HIGH | MEDIUM | LOW
      guardrail:
  effect_on_analysis:
    - tightened_claim_language
    - raised_evidence_threshold
    - blocked_known_bad_inference
```

## Decision impact

Lessons learned can legitimately influence:

- confidence level;
- required evidence before `GO`;
- whether the next step is `RESEARCH` instead of report drafting;
- whether `NO-GO` should be recorded and explained;
- which prohibited inference must be documented.

## Relationship with the finding gate

This capability complements the KAG-oriented finding validation flow.

- KAG answers whether the current case proves a qualifying break.
- Institutional learning answers whether the reasoning path is repeating a known mistake or missing a known guardrail.

Used together, they help prevent:

- technical primitive -> vulnerability inflation;
- observed behavior -> impact inflation;
- prior anecdote -> current-case conclusion.

## Security QA role

Security QA should verify that:

- relevant lessons were consulted when the case resembles a known failure mode;
- prior precedent was not treated as direct proof;
- the final conclusion reflects both current evidence and institutional guardrails;
- new lessons are captured when the engagement reveals a reusable methodological rule.

## Public repository boundary

This public repository documents the capability, operating contract, and templates.

It does not need to publish:

- private evidence;
- confidential engagement history;
- sensitive memories or raw operator notes.

A sanitized public overlay can still expose the methodology:

- when to retrieve lessons learned;
- how they constrain reasoning;
- how they feed `GO` / `RESEARCH` / `NO-GO` decisions;
- how QA validates correct use.

## Practical summary

MiniCISO's lessons-learned capability means it can:

1. look at prior institutional experience before analyzing a case;
2. test whether the current reasoning repeats a known analytical error;
3. tighten claims and evidence thresholds accordingly;
4. record new reusable lessons when an engagement teaches something durable.

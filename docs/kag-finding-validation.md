# KAG-Oriented Finding Validation

This document defines the mandatory pre-submission validation gate for MiniCISO and bug bounty findings.

## Objective

Use KAG to prevent technical primitives, expected product behavior, or theoretical impact from being promoted into qualifying vulnerabilities without sufficient evidence.

The KAG role at this stage is not only to retrieve general vulnerability knowledge. It must connect:

- observed behavior;
- intended product behavior;
- relevant trust boundary;
- program rules and exclusions;
- required impact;
- available evidence;
- remaining evidence gaps;
- submission decision.

The operating goal is:

> Prove qualifying impact or block submission.

## Core principle

No finding may be approved only because:

- a technical primitive was demonstrated;
- the behavior looks dangerous;
- a known theoretical impact exists for the class;
- the write-up is technically strong;
- the behavior could, under some conditions, lead to compromise.

Treat these relations as mandatory:

```text
technical primitive ≠ vulnerability
observed behavior ≠ impact
potential capability ≠ demonstrated exploitation
possible access ≠ proven access
well-written report ≠ valid finding
```

## Validation hypothesis

For each finding, KAG must evaluate the complete hypothesis:

> Given the observed behavior, product function, program rules, vulnerability class, and collected evidence, is there a demonstrated and qualifying security break?

Do not start with only:

> Is this SSRF, IDOR, XSS, unsafe deserialization, or another class?

Start with:

> What makes this behavior a qualifying vulnerability for this specific program, and was that condition actually proven?

## Minimum knowledge structure

Validation must consider four linked knowledge sets.

### 1. Scope Graph

It must include:

- included assets;
- excluded assets;
- non-qualifying vulnerability classes;
- program-specific impact requirements;
- test limitations;
- safe-harbor rules;
- provided examples;
- accepted severity patterns;
- conditions for reconsideration.

### 2. Vulnerability Graph

It must relate:

- technical primitive;
- preconditions;
- expected product behavior;
- relevant trust boundary;
- expected security controls;
- possible abuse paths;
- confidentiality, integrity, and availability impacts;
- difference between legitimate behavior and abusive behavior.

### 3. Evidence Graph

Every material claim must be linked to the evidence that supports it.

Examples:

```text
claim: backend performed a request
evidence: callback recorded

claim: redirect was followed
evidence: request observed at final destination

claim: internal resource was accessed
evidence: content, status, or effect unique to that resource

claim: sensitive data was exposed
evidence: reproducible and documented sensitive value
```

Evidence must never be allowed to support a stronger claim than it actually proves.

### 4. Decision Graph

It must relate:

- mandatory criteria;
- satisfied criteria;
- missing criteria;
- applicable exclusions;
- prohibited inferences;
- final decision.

Allowed decisions:

```text
GO
RESEARCH
NO-GO
```

## Gate 1 — Scope Qualification

Before deepening a finding, verify:

1. Is the vulnerability class in scope?
2. Is there an explicit exclusion?
3. Does the program require additional impact?
4. Does current evidence satisfy that requirement?
5. Is the needed impact test authorized?

Required output:

```yaml
scope_status: QUALIFIED | CONDITIONALLY_QUALIFIED | NOT_QUALIFIED
applicable_rules:
  - relevant rule or exclusion
required_impact:
  - impact required for qualification
current_evidence:
  - impact currently proven
blocking_conditions:
  - still-missing conditions
```

If the behavior falls directly into an exclusion and no exception was demonstrated, submission must be blocked.

## Gate 2 — Feature versus Vulnerability

The system must answer explicitly:

> Does the observed behavior violate a security boundary, or does it only execute the expected product function?

Identify:

- the legitimate feature goal;
- the behavior necessary for the feature to work;
- the expected security control;
- the difference between legitimate flow and abusive flow;
- the additional attacker capability gained;
- the consequence that is impossible through normal authorized use.

Required output:

```yaml
expected_behavior:
security_boundary:
boundary_violation:
attacker_advantage:
security_consequence:
```

If `boundary_violation` or `security_consequence` cannot be filled with demonstrated facts, the finding is not ready.

## Gate 3 — Impact Closure

The system must complete, without speculative language, this sentence:

> Because of this behavior, an attacker can [concrete action], causing [observable consequence], which would not be possible through normally authorized functionality.

Do not accept closure phrases such as:

- potentially;
- may allow;
- could lead to;
- might expose;
- depending on internal configuration;
- could possibly reach;
- theoretically enables.

Those terms may exist in a research hypothesis, but not as the primary basis for submission.

Required output:

```yaml
concrete_action:
observable_consequence:
security_property_affected:
unauthorized_capability:
demonstrated: true | false
```

If `demonstrated` is `false`, the decision cannot be `GO`.

## Gate 4 — Evidence Sufficiency

For every report claim:

1. What evidence supports it?
2. Is the evidence direct or inferred?
3. Is there a legitimate alternative explanation?
4. Does the evidence prove behavior, reach, or impact?
5. Does the report text exceed the strength of the evidence?

Classification:

```text
DIRECT
SUPPORTED_INFERENCE
SPECULATIVE
UNSUPPORTED
```

Claims classified as `SPECULATIVE` or `UNSUPPORTED` cannot support the title, impact, severity, or recommendation to submit.

## Gate 5 — Adversarial QA

QA must behave like a hostile triager toward the finding itself.

Its first job is not to improve the wording. Its first job is to reject the finding if possible because of:

- expected behavior;
- lack of impact;
- explicit exclusion;
- no trust-boundary break;
- insufficient evidence;
- unrealistic precondition;
- privilege requirement incompatible with the claimed impact;
- duplication of already authorized capability;
- incorrect classification;
- inflated severity;
- hypothesis presented as fact.

Required output:

```yaml
strongest_rejection_argument:
program_rule_supporting_rejection:
missing_evidence:
alternative_legitimate_explanation:
submission_decision:
```

Only after QA fails to reject the finding should it review clarity, quality, and writing.

## Impact Validator role

Add an explicit function between discovery and report generation.

Responsibility:

> Convert technical primitives into verifiable, safe, authorized, scope-compatible impact scenarios; or conclude that the primitive does not support a finding.

Flow:

```text
Primitive discovered
        ↓
Scope qualification
        ↓
Feature-versus-vulnerability analysis
        ↓
Impact hypotheses
        ↓
Safe and authorized validation
        ↓
Impact demonstrated?
   ┌────┴────┐
   │         │
  No        Yes
   │         │
RESEARCH   Adversarial QA
or NO-GO      │
              ↓
            Report
```

The Impact Validator must:

- generate impact hypotheses;
- prioritize hypotheses by lowest risk and highest evidentiary value;
- respect scope strictly;
- distinguish authorized testing from invasive action;
- stop when the next step is not authorized;
- record clearly when impact was not demonstrated.

## Mandatory artifact before submission

Every finding must generate a decision artifact similar to:

```yaml
finding_class:
primitive_demonstrated:
expected_product_behavior:
security_boundary:
scope_status:
applicable_exclusions:
required_impact:
demonstrated_impact:
evidence_strength:
remaining_gaps:
prohibited_inferences:
qa_rejection_attempt:
final_decision: GO | RESEARCH | NO-GO
decision_rationale:
```

## Decision rules

### GO

Use only when:

- the asset is in scope;
- the class is qualifying;
- no exclusion invalidates the finding;
- a trust boundary was broken;
- impact was directly demonstrated;
- the main claims have evidence;
- QA found no strong rejection argument.

### RESEARCH

Use when:

- a relevant technical primitive exists;
- impact has not yet been demonstrated;
- a plausible qualification hypothesis exists;
- additional tests are safe and authorized;
- current evidence does not yet support submission.

### NO-GO

Use when:

- the behavior is expected;
- the program explicitly excludes the case;
- no impact exists beyond the primitive;
- the hypothesis depends on unverified conditions;
- the necessary test violates scope;
- no plausible path exists to a security consequence.

## Example: SSRF in a URL import feature

Expected reasoning chain:

```text
Endpoint accepts an external URL
→ the feature exists to ingest remote content

Backend performs a request
→ this proves the import mechanism works

Backend follows redirect and accepts HTTP
→ this proves additional primitive properties

Program excludes blind SSRF without impact
→ isolated external callback does not qualify

No internal service, sensitive data, or privileged action was demonstrated
→ the required impact is absent

Decision
→ RESEARCH or NO-GO
→ submission blocked
```

Expected output:

```yaml
finding_class: SSRF
primitive_demonstrated: server-side request to attacker-controlled destination
expected_product_behavior: remote media ingestion
security_boundary: not yet shown to be violated
scope_status: CONDITIONALLY_QUALIFIED
applicable_exclusions:
  - blind SSRF without direct impact
required_impact:
  - sensitive internal service access
  - sensitive information disclosure
  - security-relevant action through backend trust
demonstrated_impact: none
evidence_strength: DIRECT_FOR_CALLBACK_ONLY
prohibited_inferences:
  - internal network access based solely on external callback
  - sensitive service reachability without response or observable effect
final_decision: NO-GO
decision_rationale: primitive proven, qualifying impact absent
```

## Operating change

The system must no longer ask first:

> How do we turn this evidence into a good report?

It must ask first:

> Would this evidence survive triage as a valid finding?

Report generation must start only after a `GO` decision.

When the decision is `RESEARCH`, the system must produce an impact-validation plan.

When the decision is `NO-GO`, the system must register the lesson learned and block submission.

## Final rule

> No amount of additional evidence about the same primitive replaces the absence of impact.

Re-confirming callback, redirect behavior, protocol handling, source IP, or user agent may strengthen proof of behavior, but it does not necessarily move the finding closer to qualification.

When the blocker is missing impact, the next experiment must test a security consequence, not simply repeat the primitive demonstration.

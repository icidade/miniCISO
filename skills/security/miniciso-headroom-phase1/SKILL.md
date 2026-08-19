---
name: miniciso-headroom-phase1
description: "Use when MiniCISO needs deterministic, selection-first retrieval over large structured artifacts using the public Headroom Phase 1 toolchain."
version: 1.0.0
author: MiniCISO
license: MIT
metadata:
  hermes:
    tags: [miniciso, security, headroom, kag, retrieval, artifacts]
    related_skills: [miniciso-kag-finding-gate, miniciso-institutional-learning]
---

# MiniCISO Headroom Phase 1

## Overview

This skill packages the public Headroom Phase 1 retrieval workflow that ships with the MiniCISO overlay.

Use it when an assessment depends on a large structured artifact that is too expensive or noisy to move into the model context raw. The goal is to preserve evidence discipline while reducing token cost through deterministic, selection-first retrieval.

This skill documents *how* to use the public toolchain under `tools/headroom_phase1/`. The Python files remain useful standalone artifacts, but the skill is the operational contract that tells the `chief-of-staff` when to use them and what guardrails apply.

## When to Use

Use this skill when:

- a JSON, SBOM, SARIF, scanner export, config bundle, or log-like artifact is too large for direct review;
- you need a reproducible retrieval pack instead of ad hoc copy/paste excerpts;
- you want hypothesis-guided evidence selection before sending context to an SME;
- a MiniCISO workflow references Headroom or selective retrieval explicitly.

Do **not** use this skill when:

- the artifact is already small enough to inspect directly;
- the work product is a final report rather than an evidence-prep step;
- the available data is unstructured conversational text with no meaningful retrieval boundary.

## Public Toolchain

The public components bundled with MiniCISO are:

- `tools/headroom_phase1/hr_index_artifact.py`
- `tools/headroom_phase1/hr_kag_query.py`
- `tools/headroom_phase1/hr_selective_retrieval.py`
- `tools/headroom_phase1/hr_manual_wrapper.py`

They implement the canonical phase-1 sequence:

1. build a structural index;
2. express the retrieval hypothesis as a KAG-style query;
3. produce a deterministic retrieval pack under a token budget;
4. preserve selection reasoning and fallback behavior in logs.

## Operating Workflow

### 1. Confirm the artifact is appropriate

Before using Headroom, record:

- artifact type;
- why raw review is too expensive or noisy;
- what hypothesis or decision the retrieval pack is supposed to support;
- what would still require direct/raw verification later.

### 2. Build a structural index

Create an index first. The index is the map used for later selection, not a finding by itself.

Expected structural outputs include:

- path and ancestor information;
- local signals;
- estimated token footprint;
- stable source hash or equivalent provenance marker.

### 3. Create the retrieval hypothesis

Use a KAG-shaped query that states:

- the candidate issue or hypothesis;
- the relevant surface or boundary;
- the artifact areas most likely to contain confirming or rejecting evidence;
- negative evidence that would block the claim.

### 4. Produce a retrieval pack

Apply deterministic selection with an explicit budget. The pack should document why each chunk was included.

At minimum, preserve:

- selected chunks;
- inclusion reasons;
- token budget used;
- unselected-but-relevant areas when they matter to confidence.

### 5. Preserve evidence discipline

After retrieval, keep these boundaries explicit:

- *retrieved* does not mean *validated*;
- *missing from pack* does not mean *absent from raw artifact*;
- *compressed or optimized output* is not authoritative over raw evidence.

## Mandatory Guardrails

- Headroom is a pre-processing aid, not the source of truth.
- Any absence in the retrieval pack must remain `not_verified_in_raw` until raw evidence is checked.
- Selection-first logs and code must stay separable from confidential engagement data.
- The RTK execution-output optimizer remains non-authoritative and defaults to `shadow` mode.
- `MINICISO_EXECUTION_OUTPUT_OPTIMIZER=0` must preserve rollback to passthrough behavior.

## Relationship to Other MiniCISO Defaults

- Use `miniciso-kag-finding-gate` when the retrieved evidence is about a candidate external finding.
- Use `miniciso-institutional-learning` when prior lessons learned should shape what evidence counts as sufficient.
- Final user-facing reports still require the `security-qa` gate before delivery.

## Common Pitfalls

1. **Treating a retrieval pack as if it were raw evidence.**
   Retrieval narrows attention; it does not upgrade confidence on its own.

2. **Using Headroom before stating the hypothesis.**
   Without a retrieval hypothesis, selection becomes expensive summarization instead of disciplined evidence targeting.

3. **Overlooking negative evidence.**
   A good retrieval query should actively look for disconfirming material, not only supportive snippets.

4. **Forgetting reproducibility.**
   If the pack cannot be regenerated from the same artifact and query, it is not strong enough for serious review.

## Verification Checklist

- [ ] Artifact is large enough to justify selection-first retrieval.
- [ ] Structural index was generated before selection.
- [ ] Retrieval query records the current hypothesis and blocking evidence.
- [ ] Token budget and inclusion reasons are preserved.
- [ ] Any missing evidence is still marked `not_verified_in_raw`.
- [ ] Downstream report decisions still pass through KAG and `security-qa`.

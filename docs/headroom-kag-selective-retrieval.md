# Headroom + KAG selective retrieval

This document describes the public, sanitized layer of the Headroom evolution toward hypothesis/KAG-guided **selection-first** retrieval.

The Python components under `tools/headroom_phase1/` remain public standalone tools, but MiniCISO also ships the operational skill `miniciso-headroom-phase1` so the `chief-of-staff` can apply them as a default workflow instead of leaving them as orphaned helper files.

## Motivation

When a structured artifact dominates context cost, the next evolution is not to compress the entire file better. It is to:

```text
hypothesis -> structural selection -> minimal retrieval pack -> optional compression -> reasoning -> expansion to raw when needed
```

This replaces the less precise flow:

```text
entire artifact -> compression -> reasoning
```

## Operating contract

Mandatory rule:

- **absence from the retrieval pack is never evidence of absence in the raw artifact**;
- if the required evidence does not appear in the pack, the correct state is **`not_verified_in_raw`**;
- final claims still depend on raw-authoritative review.

## Public components in this phase

The components versioned in `tools/headroom_phase1/` are:

- `hr_index_artifact.py`: local structural index with `json_path`, `parent_path`, `ancestors`, `signals`, `estimated_tokens`, and source hash;
- `hr_kag_query.py`: hypothesis/surface-oriented query schema;
- `hr_selective_retrieval.py`: deterministic selection with budget (`token_budget`) and inclusion reasons;
- `hr_manual_wrapper.py`: execution/logging wrapper, now able to record `selection_first` metadata in shadow mode.

## Shadow mode

The initial recommendation is to run in **shadow mode**:

1. generate a structural index;
2. generate a KAG query;
3. produce a retrieval pack;
4. continue running the raw/full flow in parallel;
5. compare savings, recovered evidence, and `decision_delta`.

## RTK execution output optimizer (experimental)

A second, narrower experiment now lives beside the wrapper in `tools/headroom_phase1/`: the **RTK execution output optimizer**.

Its contract is intentionally strict:

- `raw` remains authoritative at all times;
- the optimizer runs only in **shadow mode** by default;
- the reduced view is derivative/log-only and never replaces the effective payload;
- a single env var kill switch restores baseline behavior immediately.

### Included MVP operation classes

- `git_status`
- `git_diff_stat`
- `ls`
- `find`
- `tree`
- `git_fetch`

### Explicitly excluded from this MVP

- `read_file`
- `search_files`
- `grep`
- evidence artifacts
- reports / findings
- SARIF / SBOM / PoC material
- HTTP traces
- SME or Security QA responses

### Runtime knobs

```text
MINICISO_EXECUTION_OUTPUT_OPTIMIZER=1
MINICISO_EXECUTION_OUTPUT_OPTIMIZER_MODE=shadow
MINICISO_EXECUTION_OUTPUT_OPTIMIZER_ALLOWLIST=git_status,git_diff_stat,ls,find,tree,git_fetch
```

### Rollback rule

Set `MINICISO_EXECUTION_OUTPUT_OPTIMIZER=0` to force passthrough and preserve the pre-experiment baseline without changing the wrapper's real output path.

## Minimum pack provenance

Each selected slice must preserve, at minimum:

- `json_path`
- `parent_path` or equivalent context
- `ancestors`
- `reason_selected`
- `source_sha256` or equivalent version/hash

## Useful metrics

In addition to token savings, track:

- `source_tokens_estimated`
- `selected_tokens_estimated`
- `selection_saved_tokens`
- `selection_ratio`
- `raw_expansion_rate`
- `retrieval_precision`
- `retrieval_recall`
- `false_omission_events`
- `decision_delta`

## Public scope of this repo

This repo may carry:

- selector/indexer/wrapper code;
- unit tests for the components;
- public/sanitized overlay configuration;
- methodology documentation.

This repo **must not** carry:

- real raw assessment artifacts;
- operational logs with sensitive context;
- references to specific active BBP programs;
- unsanitized findings, repros, or triage trails.

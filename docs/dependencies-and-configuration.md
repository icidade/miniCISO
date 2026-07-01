# Dependencies and Configuration

This document tracks **non-core dependencies** that the MiniCISO overlay may rely on. Treat them as optional layers on top of Hermes, not as mandatory Hermes core requirements.

## Dependency classes

### 1. Core runtime dependencies
Required for the overlay to be useful at all:
- `git`
- network access during the first installation
- the Hermes version pinned in `config/hermes-version.env`

The bootstrap delegates Python, `uv`, Node.js, and runtime dependency management to the pinned official Hermes installer.

### 2. MiniCISO overlay content dependencies
Needed to use the prompts/profiles/templates effectively:
- local file access
- terminal access
- web access for research/recon when authorized
- skill loading enabled in Hermes

### 3. Optional external tool dependencies
Used only for specific workflows. These should be documented and enabled deliberately.

## External tooling catalog

### Biguá Analyzer
**Purpose:** external structural OSS evidence source for repository health, contributor concentration, bus factor, release rhythm, and AI-influence interpretation.

**Use cases:**
- supply-chain review
- OSS dependency triage
- confidence calibration in MiniCISO reports
- Security QA support for OSS findings

**Recommended install pattern:** isolated clone + isolated venv managed by `uv`.

```bash
mkdir -p ~/tools
cd ~/tools
git clone <your-bigua-source>
cd bigua-analyzer
env -u VIRTUAL_ENV uv venv
env -u VIRTUAL_ENV uv pip install -e .
env -u VIRTUAL_ENV uv run bigua-analyzer --help
```

**Operational note:** treat Biguá as an evidence source, not a security verdict.

### Headroom
**Purpose:** optional token-saving / compression helper for large artifacts.

**Use cases:**
- pre-processing large logs
- pre-processing SBOMs, scanner output, and raw notes
- reducing context cost before human/agent review

**Guardrails:**
- use as a pre-processing aid, not source of truth
- keep rollout switchable and reversible
- validate raw vs compressed output before relying on it for report conclusions
- prefer isolated/manual canary before deeper integration

### ProjectDiscovery Cloud / passive discovery layer
**Purpose:** passive asset discovery and cloud-assisted recon support when the assessment model includes authorized external inventory work.

**Use cases:**
- passive target inventory
- authorized BBP/VDP intake support
- asset expansion before active validation gates

**Guardrails:**
- only use within explicit authorization boundaries
- keep passive and active evidence clearly separated
- document API-based dependencies outside of Hermes secrets storage docs

### Supply-chain / artifact scanning helpers
Examples you may optionally layer in later:
- Trivy
- Grype
- Syft
- Semgrep
- CodeQL

These are **workflow-dependent** and should not be treated as mandatory unless your MiniCISO method explicitly depends on them.

## Configuration model

Use `config/tooling-dependencies.example.yaml` as the repo-side declaration of expected external tooling.

Recommended rule:
- repo config describes **what the overlay expects**
- live Hermes config and secrets stay **outside the repo**

## Environment and secret handling

Do not commit:
- API keys
- auth state
- service tokens
- live environment secret files
- user- or tenant-specific identifiers

Prefer documenting placeholders such as:
- `<set-in-local-env>`
- `<configure-outside-repo>`

## Promotion checklist for a new tool dependency

Before making a new tool part of the MiniCISO overlay, verify:
- its purpose is clear
- it adds evidence quality or operational leverage
- it has a rollback path
- it does not become the single source of truth for findings
- it can be installed without mutating Hermes core
- its secrets/config are separable from the repo

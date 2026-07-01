# MiniCISO Security Profile Setup Pattern

Reference architecture for the MiniCISO/Security SME ecosystem.

## Profile set

Use this profile group when usuário asks for a personal security staff / MiniCISO capability:

- `chief-of-staff`: MiniCISO coordinator/orchestrator; routes requests, manages handoffs, and returns the final user-facing synthesis.
- `security-threat-modeling`: threat models, abuse cases, assets, trust boundaries, prioritized controls.
- `security-architecture`: security architecture/design review, IAM, secrets, logging, segmentation, crypto, resilience.
- `security-code-review`: secure code/diff/PR review with file/line evidence, severity, remediation, regression tests.
- `security-appsec-assessment`: application security assessment, authn/authz review, API/web risk triage, and remediation guidance.
- `security-compliance-mapper`: map findings and controls to security frameworks, audit evidence, and governance expectations.
- `security-offensive-security`: authorized offensive validation only; requires explicit scope/authorization for external targets.
- `security-recon-attack-surface-strategist`: authorized passive/low-noise recon, attack surface mapping, candidate hypothesis prioritization, and SME handoff.
- `security-qa`: final quality gate for scope, evidence, severity, clarity, safety, and actionability.

## Shared workspace

Recommended local workspace:

```text
/workspace/miniciso-security/
  inputs/
  drafts/
  qa/
  reports/
  templates/
  README.md
```

Configure every SME with local file access and the shared cwd:

```bash
hermes -p <profile> config set terminal.backend local
hermes -p <profile> config set terminal.cwd ~/miniciso-security
```

Recommended toolsets for security SMEs that produce artifacts:

```text
terminal, file, web, skills, memory, session_search, delegation, todo
```

## SOUL.md role boundaries

Each SME should explicitly include:

- Portuguese Brazilian responses unless asked otherwise.
- Only analyze systems, repos, docs, or targets explicitly provided/authorized by usuário.
- Do not assume access to employer/confidential/third-party systems.
- Mark non-final outputs as `DRAFT - pendente de QA`.
- Final reports must pass through `security-qa`.

For offensive-security SMEs, include stronger boundaries:

- Require explicit authorization and scope for external targets.
- No help with intrusion, persistence, evasion, credential theft, abuse against third parties, or unauthorized automation.
- Prefer methodology, defensive validation, labs/CTFs, safe local PoCs, and remediation.

## Smoke test

After creation, verify every profile with an actual Hermes invocation:

```bash
hermes -p <profile> chat -Q -q "Responda em uma única linha começando com OK: qual é o seu papel neste ecossistema MiniCISO?"
```

Expected: each profile identifies its role and constraints correctly.

## Service catalog deliverable

After creating a staff/group of profiles, a useful next deliverable is a concise service catalog PDF for the user. Suggested contents:

1. What the staff is and how coordination works.
2. Map of profiles and when to use each one.
3. Capabilities and typical outcomes per SME.
4. What constitutes a high-quality input for each service.
5. Universal intake template: objective, scope, context, artifacts, restrictions, desired output, QA requirement.
6. Workflow: intake → SME → draft → QA → final → follow-up.
7. Copy-ready prompts.

If no presentation/PDF tooling is installed, a reliable lightweight path is Python `reportlab` for PDF generation plus `pypdf` for text validation and `PyMuPDF` + Pillow for rendering a contact sheet visual QA.

Validation checklist:

- Confirm PDF page count and file size.
- Extract text and check key section/profile names exist.
- Render pages to images and inspect a contact sheet for blank pages, cut text, overlap, margin issues, and contrast.
- Deliver with `MEDIA:/absolute/path/to/file`.

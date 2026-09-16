## Cost & Context Governance

You must load and follow `cost-context-governance` for **every request**.

Mandatory behavior:
- classify every request as `conversational`, `bounded`, or `engagement` before deep execution;
- keep governance overhead minimal for simple conversation;
- create a resource/context plan before tool-heavy, delegated, investigative, implementation, or assessment work;
- preserve QA reserve for any lane that will require independent validation;
- allocate bounded child budgets and bounded child context packages;
- restrict tools by role and task;
- checkpoint or persist partial handoff before timeout-prone or budget-limited stops;
- summarize actual resource usage at closure.

This governance layer controls execution and context/resource use. It does not replace KAG, Headroom, Institutional Learning, or Security QA.

## MiniCISO Staff orchestration

When the user asks for MiniCISO or security staff work, orchestrate the MiniCISO Staff V2 operating model:

User → MiniCISO → Specialized SME → Security QA → MiniCISO → User.

Available SMEs:
- `security-threat-modeling`
- `security-architecture`
- `security-code-review`
- `security-appsec-assessment`
- `security-offensive-security`
- `security-compliance-mapper`
- `security-recon-attack-surface-strategist`
- `security-qa`

Every MiniCISO report must include, without exception:
1. Executive Summary
2. Findings
3. Recommendations
4. Assumptions
5. Confidence Level
6. Residual Risk
7. Next Steps

Final reports must pass through `security-qa` before delivery. If a request is offensive or targets an external system, require explicit authorization, target scope, limits, and safe operating boundaries before proceeding.

## Output encoding

When generating Markdown reports in PT-BR for the user, write `.md` files as UTF-8 with BOM (`utf-8-sig`). This prevents accent mojibake in Telegram/mobile/desktop viewers. Before delivery/package, verify `file -bi <report>` reports UTF-8 and `xxd -l 3 -p <report>` returns `efbbbf`.

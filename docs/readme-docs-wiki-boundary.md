# README vs docs vs Wiki

This project uses three public documentation layers with different jobs.

## README

The `README.md` is the technical landing page.

It should stay short and discovery-oriented:
- what MiniCISO is;
- what it is not;
- quick restore;
- essential validation and smoke-test commands;
- high-signal links into the rest of the documentation.

The README should not become the full manual.

## docs/

The `docs/` directory contains canonical, versioned project documents that must evolve with the implementation.

Examples:
- operating model;
- profile contract;
- installation and runtime constraints;
- KAG/finding-validation rules;
- self-update policy;
- follow-up workflows.

When a statement is normative, implementation-coupled, or should be reviewed in PRs alongside code/config changes, it belongs in `docs/`.

## Wiki

The GitHub Wiki is the editorial and explanatory layer.

It should:
- explain concepts;
- connect documents into guided reading paths;
- provide human-friendly architecture narratives;
- document playbooks and troubleshooting;
- offer sanitized examples.

The wiki should not duplicate canonical documents line by line. Instead, wiki pages should explain and link back to the source of truth.

Recommended note:

> This page is explanatory. The canonical specification is maintained in `docs/...`.

## Practical rule

- **Normative and version-sensitive** -> repository (`README.md`, `docs/`, templates, scripts)
- **Explanatory and navigational** -> wiki
- **Private or operational state** -> never publish in either location

## Public-content guardrails

Do not publish:
- secrets or tokens;
- internal hostnames or private URLs;
- sessions, memories, or local logs;
- real client evidence;
- unsanitized reports or triage trails.

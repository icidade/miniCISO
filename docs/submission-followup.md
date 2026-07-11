# External Submission Follow-up Workflow

Use this workflow after a finding is already submitted and the job shifts from research to operational follow-up.

## Goal

Preserve context, recover traceability from local artifacts, and prepare short triage-ready replies without reopening the entire hunting lane.

## When to use

Use this workflow when:
- multiple submitted reports need one tracker;
- a triager may reply asynchronously and the operator wants fast context recovery;
- local artifacts exist but dates, URLs, or report IDs are partially missing;
- the task is follow-up coordination, not fresh validation.

Do not use it when:
- the finding has not passed the pre-submission `GO` gate yet;
- the task is still active impact validation;
- the operator wants a new report drafted from scratch.

## Operating steps

1. **Load the current state**
   - read the existing tracker if present;
   - search prior session history for packaging/submission context;
   - search the workspace for drafts, sent packs, gate notes, PoCs, and public links.

2. **Recover only verifiable metadata**
   For each report, try to recover:
   - program / target;
   - current status;
   - submission date;
   - source repository URL and commit SHA;
   - local artifact paths;
   - public PoC links;
   - platform report URL / ID.

   If something cannot be recovered, label it explicitly as missing instead of guessing.

3. **Separate grounded traceability from administrative gaps**
   Track both:
   - grounded local evidence (drafts, sent packs, gate notes, PoCs);
   - unresolved admin metadata (platform URL, report ID, exact submission timestamp).

4. **Write a follow-up tracker**
   Recommended sections:
   - Executive Summary
   - Findings
   - Recommendations
   - Assumptions
   - Confidence Level
   - Residual Risk
   - Next Steps

   Each finding should capture:
   - current status;
   - priority;
   - grounded artifacts and links;
   - likely triage dispute;
   - preferred response stance.

5. **Write response-ready triage fragments**
   Create a second artifact with one short response per likely objection class, such as:
   - "works as documented / caller misuse";
   - "helper only / not security";
   - "shared behavior is expected";
   - "local crash only".

   Keep replies short, conservative, and copy-paste-ready.

6. **Verify PT-BR Markdown encoding when applicable**
   For PT-BR reports intended for Telegram/mobile viewers, save as UTF-8 with BOM and verify:

   ```bash
   file -bi report.md
   xxd -l 3 -p report.md
   ```

   Expected BOM bytes:

   ```text
   efbbbf
   ```

## Common pitfalls

1. **Inventing report IDs or URLs**
   Never fabricate platform identifiers or exact submission dates.

2. **Treating local file mtime as platform submission time**
   A local draft timestamp is only a local artifact timestamp unless corroborated elsewhere.

3. **Reopening research unnecessarily**
   Follow-up mode is for context preservation and response readiness, not for restarting the hunt.

4. **Overwriting the main claim during triage**
   Keep replies anchored to the exact trust boundary, observed consequence, and available evidence.

## Minimal verification checklist

- [ ] Existing tracker reviewed or created
- [ ] Session history searched
- [ ] Local artifacts searched
- [ ] Missing metadata labeled explicitly
- [ ] Tracker written
- [ ] Response-fragment artifact written
- [ ] UTF-8/BOM verified when required

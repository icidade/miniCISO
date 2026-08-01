# Zenodo draft workflow

This stdlib-only Python tool validates the Evidence Closure Loop whitepaper and manages
an unpublished Zenodo deposition. It defaults to Zenodo Sandbox and never publishes
after creating or uploading a draft.

The metadata source is
`docs/whitepapers/evidence-closure-loop/zenodo.json`. The PDF is stored beside it.
The versioned DOCX is the editable source for the PDF. The author selected Creative
Commons Attribution 4.0 International (`cc-by-4.0`). Affiliation and ORCID are
optional and were omitted because they were not present in the supplied source.

## Token and environment

Create a separate account/token at <https://sandbox.zenodo.org/account/settings/applications/tokens/new/>.
For draft creation and upload, grant only `deposit:write`. A future production token
used for publication also needs `deposit:actions`. Never pass a token on the command
line: the tool reads it only from `ZENODO_ACCESS_TOKEN`.

PowerShell:

```powershell
$secureToken = Read-Host "Zenodo token" -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try {
    $env:ZENODO_ACCESS_TOKEN =
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    Remove-Variable secureToken
}
$env:ZENODO_ENV = "sandbox"
```

Bash:

```bash
read -rs ZENODO_ACCESS_TOKEN
export ZENODO_ACCESS_TOKEN
export ZENODO_ENV=sandbox
```

Sandbox is the default when `ZENODO_ENV` is absent. Production create/upload
mutations require both explicit `--environment production` and
`--allow-production`. Use a token created in the environment being addressed:
sandbox and production accounts/tokens are separate.

## Validate, create, upload, and inspect

From the repository root:

```powershell
python tools/zenodo_deposit/zenodo_deposit.py validate
python tools/zenodo_deposit/zenodo_deposit.py create-draft
python tools/zenodo_deposit/zenodo_deposit.py upload
python tools/zenodo_deposit/zenodo_deposit.py inspect
```

`validate` is offline. It checks the metadata, `%PDF` signature, file size, and
SHA-256 and prints a sanitized submission summary.

`create-draft` creates an empty deposition, immediately saves its non-secret ID and
links to the ignored `.zenodo-state.json`, then sends the metadata with
`prereserve_doi=true`. It prints the reserved DOI and browser URL. If valid local
state already points to a draft, the command resumes or reuses that draft rather
than creating another. Missing/stale state is treated as ambiguous and is not
silently replaced.

`upload` streams the PDF to the bucket URL supplied by Zenodo, retrieves the draft,
and checks filename, size, and the remote checksum when provided. It never
publishes. If a different remote file already has the same name, replacement
requires `--replace` and the exact interactive phrase shown by the tool. Replacement
is only intended for an unpublished draft.

`inspect` is read-only. It displays essential metadata, files, reserved DOI, state,
and browser link, then reports local/remote metadata differences. You may supply an
explicit ID with `--deposition-id ID`; it must agree with local state when state
exists.

Review the result in the browser using the printed `draft_url`. A reserved DOI is
also available under `metadata.prereserve_doi.doi` in the inspect response. A
reserved DOI is not registered or usable until the record is published.

## Put the reserved DOI into the PDF

The editable source is
`docs/whitepapers/evidence-closure-loop/evidence-closure-loop-whitepaper.docx`.
The deterministic OOXML updater adds the reserved DOI to the existing license line
without rewriting the document:

```powershell
python tools/zenodo_deposit/update_whitepaper_frontmatter.py `
  docs/whitepapers/evidence-closure-loop/evidence-closure-loop-whitepaper.docx `
  docs/whitepapers/evidence-closure-loop/evidence-closure-loop-whitepaper.docx `
  --doi 10.5281/zenodo.EXAMPLE
```

Replace the example with the DOI returned by the production draft. Regenerate the
PDF from that DOCX and visually review every page before upload.

After reserving the DOI:

1. update the versioned DOCX with the reserved production DOI;
2. export it again as
   `docs/whitepapers/evidence-closure-loop/evidence-closure-loop-whitepaper.pdf`;
3. run `validate`;
4. run `upload --replace` against the same unpublished draft and type the requested
   replacement confirmation;
5. run `inspect` and review the draft in Zenodo's web interface.

Do not patch the current PDF binary in place.

## Future manual publication

Publication is intentionally a separate production-only operation:

```powershell
python tools/zenodo_deposit/zenodo_deposit.py publish `
  --publish `
  --environment production `
  --deposition-id 123456
```

Before the publish request, the tool validates the local files, retrieves the
production draft, confirms matching metadata and PDF, confirms a reserved DOI,
checks Zenodo's returned publish link, rejects CI, prints a final summary, and
requires typing `PUBLISH 123456`.

Publishing registers the DOI and makes the record public. It is not automatically
reversible. This command must only be run after human review and explicit
authorization; it is never invoked by tests or CI.

Official API reference: <https://developers.zenodo.org/>

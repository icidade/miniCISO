# Adversarial Finding Validation Prompt

Use this prompt before approving any bug bounty or external submission draft.

## Prompt

You are validating a candidate security finding for MiniCISO.

Your job is **not** to improve the report first.
Your first job is to determine whether the observed behavior survives triage as a qualifying finding for the specific program.

Apply KAG-oriented validation with the following mandatory order:

1. Scope Qualification
2. Feature versus Vulnerability
3. Impact Closure
4. Evidence Sufficiency
5. Adversarial QA

You must reason over:

- observed behavior
- expected product function
- relevant trust boundary
- program scope and exclusions
- impact required by the program
- direct evidence
- missing evidence
- safe and authorized next tests

Mandatory rules:

- A technical primitive is not enough.
- Expected behavior is not enough.
- Theoretical impact is not enough.
- A well-written report is not enough.
- If impact is not demonstrated, do not approve submission.
- If the case is explicitly excluded unless additional impact exists, require that impact to be proven.
- Do not let evidence support a stronger claim than it actually proves.
- Do not rewrite speculative claims into confident language.
- If the finding is not ready, block submission and say why.

Return exactly these sections:

## Decision Artifact
Provide the completed structure from `templates/finding-decision-template.md`.

## Rejection Attempt
State the strongest rejection argument a hostile triager would likely use.

## Decision
Choose exactly one:
- GO
- RESEARCH
- NO-GO

## If RESEARCH
Provide only the safest, highest-evidentiary-value next validation steps that remain within authorized scope.
The plan must state:
- missing proof
- authorized next test
- evidentiary goal
- safety check
- explicit stop condition

## If NO-GO
State the lesson learned and the prohibited inference that must not be repeated.

## Hard stop conditions
Do not approve `GO` unless all are true:

- the asset is in scope;
- the class is qualifying;
- no exclusion invalidates the current evidence;
- a trust boundary was actually broken;
- security impact was directly demonstrated;
- the main claims are backed by evidence;
- QA cannot reject the finding with a stronger simpler explanation.

You must also complete a final `go_checklist` with one boolean per condition.
If any checklist value is `false`, `final_decision` cannot be `GO`.

Additional enforcement rules:
- `RESEARCH` cannot be used if the only planned work is stronger proof of the same primitive.
- A title must not claim more than the strongest `DIRECT` or `SUPPORTED_INFERENCE` evidence.
- If `final_decision != GO`, do not draft an external report title.

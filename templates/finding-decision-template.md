# Finding Decision Artifact

Use this template before drafting any external vulnerability report.

```yaml
finding_id:
target_program:
asset:
endpoint_or_surface:
finding_class:
research_phase:

primitive_demonstrated:
expected_product_behavior:
security_boundary:
feature_or_vulnerability:

scope_status: QUALIFIED | CONDITIONALLY_QUALIFIED | NOT_QUALIFIED
applicable_rules:
applicable_exclusions:
required_impact:
current_evidence:
blocking_conditions:
allowed_validation_boundary:

boundary_violation:
attacker_advantage:
security_consequence:
concrete_action:
observable_consequence:
security_property_affected:
unauthorized_capability:
demonstrated: true | false

claims:
  - claim:
    evidence:
    strength: DIRECT | SUPPORTED_INFERENCE | SPECULATIVE | UNSUPPORTED
    alternative_explanation:

remaining_gaps:
prohibited_inferences:
impact_hypotheses:
  - hypothesis:
    evidentiary_value:
    safety:
    status: OPEN | TESTED | BLOCKED | REJECTED | CONFIRMED

research_plan:
  missing_proof:
  authorized_next_test:
  evidentiary_goal:
  safety_check:
  stop_if:
  owner_decision_date:

qa_rejection_attempt:
  strongest_rejection_argument:
  program_rule_supporting_rejection:
  missing_evidence:
  alternative_legitimate_explanation:
  submission_decision:

go_checklist:
  in_scope: true | false
  qualifying_class: true | false
  no_exclusion_blocks: true | false
  trust_boundary_broken: true | false
  impact_directly_demonstrated: true | false
  claims_backed_by_evidence: true | false
  qa_rejection_overcome: true | false

final_decision: GO | RESEARCH | NO-GO
decision_rationale:
lesson_learned:
repeat_error_to_avoid:
next_action:
```

## Minimum acceptance rules

- `final_decision: GO` requires demonstrated impact.
- `SPECULATIVE` or `UNSUPPORTED` claims cannot support title, impact, or severity.
- If the case depends on conditions not directly evidenced, default to `RESEARCH` or `NO-GO`.
- If the program explicitly excludes the demonstrated behavior, default to `NO-GO` unless an allowed exception is also demonstrated.
- If the observed behavior is an expected feature, the artifact must explain the exact boundary violation and the attacker-only advantage; otherwise the finding is not ready.
- `RESEARCH` cannot be used when the only planned work is stronger proof of the same primitive.
- A title must not claim more than the strongest `DIRECT` or `SUPPORTED_INFERENCE` evidence.
- If `final_decision != GO`, do not draft an external report title.

## Output contract

- `GO` → report drafting may begin.
- `RESEARCH` → produce a safe impact-validation plan.
- `NO-GO` → block submission and register the lesson learned.

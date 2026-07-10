#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ALIASES = {
    "github-actions": ["actions", "workflow", "release", "publish"],
    "auth-session": ["auth", "session", "login", "permission"],
    "supply-chain": ["supply-chain", "build", "artifact", "publish", "release"],
}


def normalize_list(values: list[str] | None) -> list[str]:
    return [value.strip() for value in (values or []) if value and value.strip()]


def infer_tags(surface: str, question: str, impact_target: str, anti_goals: list[str], required_evidence_types: list[str]) -> list[str]:
    tags = set(normalize_list([surface]))
    surface_aliases = ALIASES.get(surface, [])
    tags.update(surface_aliases)

    haystack = " ".join([question, impact_target, *anti_goals, *required_evidence_types]).lower()
    for token in ["publish", "release", "actions", "workflow", "auth", "session", "permission", "secret", "artifact", "build"]:
        if token in haystack:
            tags.add(token)
    return sorted(tags)


def build_query(
    *,
    surface: str,
    question: str,
    impact_target: str,
    token_budget: int,
    anti_goals: list[str] | None = None,
    required_evidence_types: list[str] | None = None,
    confidence_threshold: str = "medium",
    raw_expansion_policy: str = "expand_on_missing_required_evidence",
    boundary: str | None = None,
    target_claim: str | None = None,
) -> dict:
    anti_goals = normalize_list(anti_goals)
    required_evidence_types = normalize_list(required_evidence_types)
    return {
        "surface": surface.strip(),
        "boundary": (boundary or "").strip(),
        "question": question.strip(),
        "target_claim": (target_claim or question).strip(),
        "impact_target": impact_target.strip(),
        "anti_goals": anti_goals,
        "required_evidence_types": required_evidence_types,
        "token_budget": int(token_budget),
        "confidence_threshold": confidence_threshold.strip(),
        "raw_expansion_policy": raw_expansion_policy.strip(),
        "tags": infer_tags(surface.strip(), question, impact_target, anti_goals, required_evidence_types),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a KAG query schema for selective retrieval.")
    parser.add_argument("output", help="Path to output JSON query")
    parser.add_argument("--surface", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--impact-target", required=True)
    parser.add_argument("--token-budget", type=int, required=True)
    parser.add_argument("--boundary", default="")
    parser.add_argument("--target-claim", default="")
    parser.add_argument("--anti-goal", action="append", default=[])
    parser.add_argument("--required-evidence-type", action="append", default=[])
    parser.add_argument("--confidence-threshold", default="medium")
    parser.add_argument("--raw-expansion-policy", default="expand_on_missing_required_evidence")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_query(
        surface=args.surface,
        question=args.question,
        impact_target=args.impact_target,
        token_budget=args.token_budget,
        anti_goals=args.anti_goal,
        required_evidence_types=args.required_evidence_type,
        confidence_threshold=args.confidence_threshold,
        raw_expansion_policy=args.raw_expansion_policy,
        boundary=args.boundary,
        target_claim=args.target_claim,
    )
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

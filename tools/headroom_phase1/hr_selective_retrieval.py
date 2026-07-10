#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def score_node(node: dict[str, Any], query: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    signals = set(node.get("signals", []))
    tags = {tag.lower() for tag in query.get("tags", [])}
    anti_goals = " ".join(query.get("anti_goals", [])).lower()
    surface = query.get("surface")
    path_text = node.get("json_path", "").lower()
    preview = node.get("content_preview", "")
    preview_text = preview.lower()

    if anti_goals and any(token in preview_text or token in path_text for token in anti_goals.split() if len(token) > 3):
        return -1000, ["anti_goal_match"]

    if "dependency_graph_sbom.data.sbom.packages[" in path_text and path_text.endswith(".name") and surface != "supply-chain":
        return -250, ["noise:sbom_package_name_outside_supply_chain"]

    for signal in sorted(signals):
        normalized = signal.removeprefix("keyword:")
        if normalized in tags:
            score += 10
            reasons.append(f"signal:{signal}")

    required_terms = " ".join(query.get("required_evidence_types", [])).lower()
    for token in ["permission", "secret", "publish", "workflow", "auth", "session", "artifact", "build"]:
        if token in required_terms and (token in preview_text or token in path_text or f"keyword:{token}" in signals):
            score += 5
            reasons.append(f"required:{token}")

    if surface == "github-actions":
        if "workflow" in path_text or "actions" in path_text or "release" in path_text:
            score += 4
            reasons.append("surface:github-actions")
        if "dependency_graph_sbom" in path_text:
            score -= 30
            reasons.append("penalty:sbom_for_actions")

    if surface == "auth-session":
        if any(term in path_text for term in ["auth", "session", "permission"]):
            score += 6
            reasons.append("surface:auth-session")
        if "dependency_graph_sbom" in path_text:
            score -= 30
            reasons.append("penalty:sbom_for_auth")

    if surface == "supply-chain":
        if any(term in path_text for term in ["release", "publish", "artifact", "package", "sbom"]):
            score += 6
            reasons.append("surface:supply-chain")

    if "release" in path_text or "publish" in path_text:
        score += 3
        reasons.append("path:release_or_publish")

    return score, sorted(set(reasons))


def build_retrieval_pack(index_doc: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    budget = int(query["token_budget"])
    scored = []
    for node in index_doc.get("nodes", []):
        score, reasons = score_node(node, query)
        if score <= 0:
            continue
        scored.append((score, node, reasons))
    scored.sort(key=lambda item: (-item[0], item[1].get("estimated_tokens", 0), item[1].get("json_path", "")))

    selected = []
    selected_tokens = 0
    for score, node, reasons in scored:
        estimated = int(node.get("estimated_tokens", 0))
        if selected and selected_tokens + estimated > budget:
            continue
        if not selected and estimated > budget:
            continue
        selected_tokens += estimated
        selected.append(
            {
                "json_path": node["json_path"],
                "node_type": node.get("node_type"),
                "ancestors": node.get("ancestors", []),
                "estimated_tokens": estimated,
                "signals": node.get("signals", []),
                "reason_selected": reasons,
                "content_preview": node.get("content_preview", ""),
                "score": score,
            }
        )

    source_tokens = sum(int(node.get("estimated_tokens", 0)) for node in index_doc.get("nodes", []))
    return {
        "query": query,
        "source": index_doc.get("source", {}),
        "selected_slices": selected,
        "selection_metrics": {
            "source_tokens_estimated": source_tokens,
            "selected_tokens_estimated": selected_tokens,
            "selection_saved_tokens": max(0, source_tokens - selected_tokens),
            "selection_ratio": 0 if source_tokens == 0 else round(selected_tokens / source_tokens, 6),
        },
        "fallback": {
            "raw_retrieval_available": True,
            "raw_required_for_final_claims": True,
            "absence_semantics": "not_verified_in_raw",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a selective retrieval pack from an index and a KAG query.")
    parser.add_argument("index", help="Path to artifact index JSON")
    parser.add_argument("query", help="Path to query JSON")
    parser.add_argument("output", help="Path to output retrieval pack JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_doc = json.loads(Path(args.index).read_text(encoding="utf-8"))
    query_doc = json.loads(Path(args.query).read_text(encoding="utf-8"))
    pack = build_retrieval_pack(index_doc, query_doc)
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shlex
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json_maybe(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def top_level_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(value.keys())
    return []


def build_selection_metadata(
    *,
    index_path: str | Path | None = None,
    query_path: str | Path | None = None,
    pack_path: str | Path | None = None,
    mode: str = "shadow",
) -> dict[str, Any]:
    if not index_path or not query_path or not pack_path:
        return {"enabled": False}

    index_doc = json.loads(Path(index_path).read_text(encoding="utf-8"))
    query_doc = json.loads(Path(query_path).read_text(encoding="utf-8"))
    pack_doc = json.loads(Path(pack_path).read_text(encoding="utf-8"))
    selected_slices = pack_doc.get("selected_slices", [])
    all_reasons = sorted(
        {
            reason
            for slice_ in selected_slices
            for reason in slice_.get("reason_selected", [])
        }
    )

    return {
        "enabled": True,
        "mode": mode,
        "index_path": str(Path(index_path).resolve()),
        "query_path": str(Path(query_path).resolve()),
        "pack_path": str(Path(pack_path).resolve()),
        "surface": query_doc.get("surface", ""),
        "boundary": query_doc.get("boundary", ""),
        "token_budget": query_doc.get("token_budget"),
        "required_evidence_types": query_doc.get("required_evidence_types", []),
        "source_path": index_doc.get("source", {}).get("path"),
        "source_sha256": index_doc.get("source", {}).get("sha256"),
        "index_summary": index_doc.get("summary", {}),
        "selection_metrics": pack_doc.get("selection_metrics", {}),
        "selected_slice_count": len(selected_slices),
        "top_selected_paths": [slice_.get("json_path") for slice_ in selected_slices[:10]],
        "top_selection_reasons": all_reasons[:10],
        "fallback": pack_doc.get("fallback", {}),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manual Headroom Phase 1 wrapper with evidence logging.")
    p.add_argument("input", help="Input text artifact path")
    p.add_argument("output", help="Output compressed artifact path")
    p.add_argument("--artifact-type", default="generic", help="Artifact class, e.g. sbom/json/report")
    p.add_argument("--role", default="user", choices=["user", "assistant"], help="Message role for Headroom API")
    p.add_argument("--encoding", default="utf-8", help="Input/output text encoding")
    p.add_argument("--model", default="gpt-4o-mini", help="Model label for token counting")
    p.add_argument("--model-limit", type=int, default=128000, help="Context window for token counting")
    p.add_argument("--target-ratio", type=float, default=0.2, help="Target ratio for compression")
    p.add_argument("--compress-user-messages", action="store_true", help="Allow user messages to be compressed")
    p.add_argument("--protect-recent", type=int, default=0, help="Protect N recent messages from compression")
    p.add_argument("--returned-to-raw", choices=["yes", "no"], default="no", help="Whether operator returned to raw evidence after compression")
    p.add_argument(
        "--raw-retrieval-required",
        choices=["yes", "no", "auto"],
        default="auto",
        help="Whether raw retrieval was required for safe use/QA of this artifact",
    )
    p.add_argument(
        "--qa-verdict",
        choices=["better", "equal", "worse", "blocker", "unknown"],
        default="unknown",
        help="Human/QA verdict for this artifact run",
    )
    p.add_argument("--note", default="", help="Free-form operator note")
    p.add_argument("--log-dir", default="/home/vpsadmin/miniciso-security/headroom_phase1/logs", help="Log directory")
    p.add_argument("--selection-index", default="", help="Path to structural index JSON for selection-first shadow mode")
    p.add_argument("--selection-query", default="", help="Path to KAG query JSON for selection-first shadow mode")
    p.add_argument("--selection-pack", default="", help="Path to retrieval pack JSON for selection-first shadow mode")
    p.add_argument("--selection-mode", default="shadow", choices=["shadow", "primary"], help="Whether selection-first is running in shadow mode or primary mode")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    log_dir = Path(args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    runs_jsonl = log_dir / "headroom_phase1_runs.jsonl"
    run_json = log_dir / f"{run_id}.json"

    raw_bytes = input_path.read_bytes()
    raw_sha256 = sha256_hex(raw_bytes)
    text = raw_bytes.decode(args.encoding, errors="replace")
    raw_json = parse_json_maybe(text)
    raw_top_level_keys = top_level_keys(raw_json)

    enabled = os.getenv("MINICISO_HEADROOM_ENABLED", "1") != "0"
    command_used = "MINICISO_HEADROOM_ENABLED=%s %s" % (
        os.getenv("MINICISO_HEADROOM_ENABLED", "1"),
        " ".join(shlex.quote(part) for part in sys.argv),
    )

    started = time.time()
    if enabled:
        from headroom import compress

        result = compress(
            [{"role": args.role, "content": text}],
            model=args.model,
            model_limit=args.model_limit,
            target_ratio=args.target_ratio,
            compress_user_messages=args.compress_user_messages,
            protect_recent=args.protect_recent,
        )
        output_text = result.messages[0]["content"]
        tokens_before = result.tokens_before
        tokens_after = result.tokens_after
        tokens_saved = result.tokens_saved
        compression_ratio = result.compression_ratio
        transforms_applied = list(result.transforms_applied)
        mode = "compressed" if tokens_saved > 0 else "noop"
    else:
        output_text = text
        tokens_before = None
        tokens_after = None
        tokens_saved = 0
        compression_ratio = 0.0
        transforms_applied = ["kill-switch-passthrough"]
        mode = "kill-switch-passthrough"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding=args.encoding)
    output_bytes = output_path.read_bytes()
    output_json = parse_json_maybe(output_text)
    output_top_level_keys = top_level_keys(output_json)
    missing_top_level_keys = sorted(set(raw_top_level_keys) - set(output_top_level_keys))
    structure_preserved = bool(raw_top_level_keys) and raw_top_level_keys == output_top_level_keys
    output_semantics = "canonical-or-noop"
    quality_flags: list[str] = []
    guard_actions: list[str] = []

    seen_raw_sha256 = set()
    if runs_jsonl.exists():
        with runs_jsonl.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    prev = json.loads(line)
                except Exception:
                    continue
                prev_raw = prev.get("raw") if isinstance(prev, dict) else None
                prev_sha = prev_raw.get("sha256") if isinstance(prev_raw, dict) else None
                if prev_sha:
                    seen_raw_sha256.add(prev_sha)

    raw_components_count = len(raw_json.get("components", [])) if isinstance(raw_json, dict) and isinstance(raw_json.get("components"), list) else None
    output_components_count = len(output_json.get("components", [])) if isinstance(output_json, dict) and isinstance(output_json.get("components"), list) else None

    if raw_top_level_keys and not output_top_level_keys:
        output_semantics = "lossy-triage-summary"
        quality_flags.append("output_not_valid_json")
    elif missing_top_level_keys:
        output_semantics = "lossy-triage-summary"
        quality_flags.append("missing_top_level_keys")

    if (
        args.artifact_type == "sbom-json"
        and raw_components_count is not None
        and output_components_count is not None
        and raw_components_count > 0
        and output_components_count < raw_components_count
    ):
        quality_flags.extend(["sbom_component_count_reduced", "raw_required_for_sbom_authority"])
        guard_actions.append("sbom_guard_reverted_to_raw")
        output_text = text
        output_path.write_text(output_text, encoding=args.encoding)
        output_bytes = output_path.read_bytes()
        output_json = raw_json
        output_top_level_keys = raw_top_level_keys
        missing_top_level_keys = []
        structure_preserved = True
        output_components_count = raw_components_count
        output_semantics = "guarded-passthrough-raw-authoritative"
        mode = "guard-passthrough"

    raw_retrieval_required = (
        args.raw_retrieval_required == "yes"
        if args.raw_retrieval_required != "auto"
        else (
            args.returned_to_raw == "yes"
            or "raw_required_for_sbom_authority" in quality_flags
            or mode == "guard-passthrough"
        )
    )
    tokens_saved_unique_artifact = 0 if raw_sha256 in seen_raw_sha256 else tokens_saved
    selection_metadata = build_selection_metadata(
        index_path=args.selection_index or None,
        query_path=args.selection_query or None,
        pack_path=args.selection_pack or None,
        mode=args.selection_mode,
    )

    elapsed_ms = round((time.time() - started) * 1000, 2)

    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "headroom_enabled": enabled,
        "kill_switch_env": os.getenv("MINICISO_HEADROOM_ENABLED", "1"),
        "mode": mode,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "artifact_type": args.artifact_type,
        "command_used": command_used,
        "returned_to_raw": args.returned_to_raw == "yes",
        "raw_retrieval_required": raw_retrieval_required,
        "qa_verdict": args.qa_verdict,
        "operator_note": args.note,
        "encoding": args.encoding,
        "raw": {
            "sha256": raw_sha256,
            "bytes": len(raw_bytes),
            "chars": len(text),
        },
        "compressed": {
            "sha256": sha256_hex(output_bytes),
            "bytes": len(output_bytes),
            "chars": len(output_text),
            "semantics": output_semantics,
        },
        "structure_checks": {
            "raw_top_level_keys": raw_top_level_keys,
            "output_top_level_keys": output_top_level_keys,
            "missing_top_level_keys": missing_top_level_keys,
            "structure_preserved": structure_preserved,
            "raw_components_count": raw_components_count,
            "output_components_count": output_components_count,
            "quality_flags": quality_flags,
            "guard_actions": guard_actions,
        },
        "headroom_metrics": {
            "model": args.model,
            "model_limit": args.model_limit,
            "target_ratio": args.target_ratio,
            "role": args.role,
            "compress_user_messages": args.compress_user_messages,
            "protect_recent": args.protect_recent,
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "tokens_saved_unique_artifact": tokens_saved_unique_artifact,
            "compression_ratio": compression_ratio,
            "transforms_applied": transforms_applied,
            "elapsed_ms": elapsed_ms,
        },
        "selection_first": selection_metadata,
    }

    run_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with runs_jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Mapping

DEFAULT_ALLOWLIST = (
    "git_status",
    "git_diff_stat",
    "ls",
    "find",
    "tree",
    "git_fetch",
)

EXCLUDED_OPERATION_CLASSES = {
    "read_file",
    "search_files",
    "grep",
    "evidence_artifact",
    "report",
    "finding",
    "sarif",
    "sbom",
    "poc",
    "http_trace",
    "sme_response",
    "security_qa_response",
}


@dataclass(frozen=True)
class OptimizerConfig:
    enabled: bool
    mode: str
    allowlist: tuple[str, ...]


@dataclass(frozen=True)
class OptimizationResult:
    operation_class: str
    enabled: bool
    mode: str
    optimizer_applied: bool
    delivered_output: str
    authoritative_raw_output: str
    reduced_output: str | None
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "operation_class": self.operation_class,
            "enabled": self.enabled,
            "mode": self.mode,
            "optimizer_applied": self.optimizer_applied,
            "delivered_output": self.delivered_output,
            "authoritative_raw_output": self.authoritative_raw_output,
            "reduced_output": self.reduced_output,
            "reason": self.reason,
        }


def _is_truthy(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", "disabled", ""}


def _normalize_mode(value: str | None) -> str:
    mode = (value or "shadow").strip().lower()
    return mode if mode in {"shadow", "passthrough"} else "shadow"


def _normalize_allowlist(raw: str | None) -> tuple[str, ...]:
    if not raw or not raw.strip():
        return DEFAULT_ALLOWLIST
    values = []
    for item in raw.split(","):
        cleaned = item.strip()
        if cleaned:
            values.append(cleaned)
    return tuple(values) or DEFAULT_ALLOWLIST


def load_optimizer_config(env: Mapping[str, str] | None = None) -> OptimizerConfig:
    env_map = env or os.environ
    return OptimizerConfig(
        enabled=_is_truthy(env_map.get("MINICISO_EXECUTION_OUTPUT_OPTIMIZER"), default=True),
        mode=_normalize_mode(env_map.get("MINICISO_EXECUTION_OUTPUT_OPTIMIZER_MODE")),
        allowlist=_normalize_allowlist(env_map.get("MINICISO_EXECUTION_OUTPUT_OPTIMIZER_ALLOWLIST")),
    )


def _head_tail(lines: list[str], *, head: int = 20, tail: int = 5) -> str:
    if len(lines) <= head + tail:
        return "\n".join(lines)
    omitted = len(lines) - (head + tail)
    return "\n".join(lines[:head] + [f"... ({omitted} lines omitted) ..."] + lines[-tail:])


def _summarize_git_status(raw_output: str) -> str:
    lines = [line.rstrip() for line in raw_output.splitlines() if line.strip()]
    modified = sum(1 for line in lines if line.startswith("modified:"))
    deleted = sum(1 for line in lines if line.startswith("deleted:"))
    untracked = sum(1 for line in lines if line.startswith("Untracked files:") or line.startswith("\t"))
    summary = {
        "kind": "git_status",
        "line_count": len(lines),
        "modified": modified,
        "deleted": deleted,
        "untracked_markers": untracked,
        "preview": _head_tail(lines, head=12, tail=4),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _summarize_git_diff_stat(raw_output: str) -> str:
    lines = [line.rstrip() for line in raw_output.splitlines() if line.strip()]
    changed_files = [line for line in lines if "|" in line]
    total_line = next((line for line in reversed(lines) if re.search(r"\d+ files? changed", line)), "")
    summary = {
        "kind": "git_diff_stat",
        "changed_files": len(changed_files),
        "total": total_line,
        "preview": _head_tail(lines, head=15, tail=2),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _summarize_listing(operation_class: str, raw_output: str) -> str:
    lines = [line.rstrip() for line in raw_output.splitlines() if line.strip()]
    summary = {
        "kind": operation_class,
        "line_count": len(lines),
        "preview": _head_tail(lines, head=25, tail=5),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _summarize_git_fetch(raw_output: str) -> str:
    lines = [line.rstrip() for line in raw_output.splitlines() if line.strip()]
    summary = {
        "kind": "git_fetch",
        "line_count": len(lines),
        "preview": _head_tail(lines, head=20, tail=4),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _build_reduced_output(operation_class: str, raw_output: str) -> str:
    if operation_class == "git_status":
        return _summarize_git_status(raw_output)
    if operation_class == "git_diff_stat":
        return _summarize_git_diff_stat(raw_output)
    if operation_class in {"ls", "find", "tree"}:
        return _summarize_listing(operation_class, raw_output)
    if operation_class == "git_fetch":
        return _summarize_git_fetch(raw_output)
    raise ValueError(f"Unsupported operation class: {operation_class}")


def optimize_output(operation_class: str, raw_output: str, env: Mapping[str, str] | None = None) -> OptimizationResult:
    config = load_optimizer_config(env)
    normalized_class = (operation_class or "").strip()
    passthrough_reason = "passthrough"

    if not config.enabled:
        return OptimizationResult(normalized_class, False, config.mode, False, raw_output, raw_output, None, "kill_switch_disabled")
    if config.mode == "passthrough":
        return OptimizationResult(normalized_class, True, config.mode, False, raw_output, raw_output, None, passthrough_reason)
    if normalized_class in EXCLUDED_OPERATION_CLASSES:
        return OptimizationResult(normalized_class, True, config.mode, False, raw_output, raw_output, None, "excluded_operation_class")
    if normalized_class not in config.allowlist:
        return OptimizationResult(normalized_class, True, config.mode, False, raw_output, raw_output, None, "not_allowlisted")

    reduced = _build_reduced_output(normalized_class, raw_output)
    return OptimizationResult(normalized_class, True, config.mode, True, raw_output, raw_output, reduced, "shadow_derivative_only")

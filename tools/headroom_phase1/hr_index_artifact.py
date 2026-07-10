#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

KEYWORD_RULES = {
    "publish": ["publish", "release", "deploy", "package"],
    "secret": ["secret", "token", "credential", "password", "key"],
    "permission": ["permission", "permissions", "privilege", "scope"],
    "workflow": ["workflow", "job", "step", "uses", "run", "checkout"],
    "auth": ["auth", "session", "login", "oauth", "cookie"],
    "supply_chain": ["artifact", "build", "container", "image", "manifest", "lockfile"],
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def estimate_tokens(value: Any) -> int:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    return max(1, len(rendered) // 4)


def node_type_for(value: Any) -> str:
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    return "scalar"


def child_path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]" if parent else f"[{key}]"
    return f"{parent}.{key}" if parent else str(key)


def collect_signals(json_path: str, value: Any) -> list[str]:
    haystack_parts = [json_path]
    if isinstance(value, dict):
        haystack_parts.extend(str(k) for k in value.keys())
        haystack_parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True)[:4000])
    elif isinstance(value, list):
        haystack_parts.append(json.dumps(value[:10], ensure_ascii=False, sort_keys=True))
    else:
        haystack_parts.append(str(value))
    haystack = " ".join(haystack_parts).lower()

    signals: list[str] = []
    for signal_name, keywords in KEYWORD_RULES.items():
        if any(keyword in haystack for keyword in keywords):
            label = signal_name[:-1] if signal_name.endswith("s") else signal_name
            if signal_name == "secret":
                label = "secret"
            elif signal_name == "publish":
                label = "publish"
            elif signal_name == "permission":
                label = "permission"
            elif signal_name == "workflow":
                label = "workflow"
            elif signal_name == "auth":
                label = "auth"
            elif signal_name == "supply_chain":
                label = "supply_chain"
            signals.append(f"keyword:{label}")
    return sorted(set(signals))


def walk(value: Any, json_path: str = "", ancestors: list[str] | None = None) -> list[dict[str, Any]]:
    ancestors = list(ancestors or [])
    current_path = json_path or "$"
    preview = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    node = {
        "json_path": current_path,
        "parent_path": ancestors[-1] if ancestors else None,
        "node_type": node_type_for(value),
        "ancestors": ancestors,
        "estimated_tokens": estimate_tokens(value),
        "signals": collect_signals(current_path, value),
        "content_preview": preview[:500],
    }
    nodes = [node]

    if isinstance(value, dict):
        for key, child in value.items():
            next_path = child_path(json_path, key)
            nodes.extend(walk(child, next_path, ancestors + ([json_path] if json_path else [])))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            next_path = child_path(json_path, index)
            nodes.extend(walk(child, next_path, ancestors + ([json_path] if json_path else [])))
    return nodes


def build_index(source_path: str | Path) -> dict[str, Any]:
    source = Path(source_path).resolve()
    raw_bytes = source.read_bytes()
    data = json.loads(raw_bytes.decode("utf-8"))
    nodes = walk(data, "", [])
    return {
        "source": {
            "path": str(source),
            "sha256": sha256_hex(raw_bytes),
            "bytes": len(raw_bytes),
        },
        "summary": {
            "root_type": node_type_for(data),
            "node_count": len(nodes),
        },
        "nodes": nodes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a structural index for a JSON artifact.")
    parser.add_argument("input", help="Path to input JSON artifact")
    parser.add_argument("output", nargs="?", help="Optional path to output index JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_index(args.input)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

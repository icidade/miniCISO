#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as exc:
    raise SystemExit("PyYAML is required; run this with the Hermes environment Python.") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge the public governance config into installed Hermes profiles.")
    parser.add_argument("--source", required=True, help="Path to config/chief-of-staff.public.yaml")
    parser.add_argument("--profile-config", action="append", required=True, help="Target profile config.yaml path")
    return parser.parse_args()


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def merge_governance(source: dict, target: dict) -> dict:
    merged = dict(target)
    merged["cost_context_governance"] = source.get("cost_context_governance", {})
    return merged


def main() -> int:
    args = parse_args()
    source = load_yaml(Path(args.source).resolve())
    if "cost_context_governance" not in source:
        raise SystemExit("Source config does not contain cost_context_governance")

    results = []
    for raw_path in args.profile_config:
        path = Path(raw_path).resolve()
        if path.parent.name != "chief-of-staff":
            raise SystemExit(f"Refusing governance merge outside chief-of-staff profile: {path.name}")
        current = load_yaml(path)
        merged = merge_governance(source, current)
        dump_yaml(path, merged)
        results.append({
            "profile_config": str(path),
            "mode": merged["cost_context_governance"].get("mode"),
            "workspace_dir": merged["cost_context_governance"].get("workspace_dir"),
        })

    print(json.dumps({"updated": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

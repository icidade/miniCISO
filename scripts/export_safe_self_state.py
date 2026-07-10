#!/usr/bin/env python3
import argparse
import re
import shutil
from pathlib import Path

import yaml

SAFE_TOOLSETS = {
    "hermes-cli",
    "terminal",
    "file",
    "web",
    "skills",
    "memory",
    "session_search",
    "delegation",
    "todo",
    "browser",
}

SUSPICIOUS_PATTERNS = [
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]+",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"Authorization:\s*Bearer",
    r"/bbp_pipeline/",
    r"/cron/output/",
    r"/memories/",
    r"/sessions/",
    r"hermes-assessment-\d{8}",
    r"active engagement",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export public/safe MiniCISO state from the VPS into this repo.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--source-workspace", default="/home/vpsadmin/miniciso-security")
    parser.add_argument("--source-profile", default="/home/vpsadmin/.hermes/profiles/chief-of-staff")
    parser.add_argument("--apply", action="store_true", help="Actually write files. Default is dry-run.")
    return parser.parse_args()


def ensure_parent(path: Path, apply: bool) -> None:
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)


def inspect_text_safety(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise SystemExit(f"blocked export: suspicious content matched {pattern!r} in {path}")


def copy_file(src: Path, dst: Path, apply: bool) -> None:
    inspect_text_safety(src)
    print(f"[{'apply' if apply else 'dry-run'}] copy {src} -> {dst}")
    if apply:
        ensure_parent(dst, apply=True)
        shutil.copy2(src, dst)


def sanitize_config(config_path: Path) -> dict:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    model = data.get("model", {}) or {}
    agent = data.get("agent", {}) or {}
    terminal = data.get("terminal", {}) or {}
    browser = data.get("browser", {}) or {}
    compression = data.get("compression", {}) or {}
    web = data.get("web", {}) or {}
    auxiliary = data.get("auxiliary", {}) or {}

    out = {
        "generated_from": "chief-of-staff/config.yaml",
        "sanitized": True,
        "profile": "chief-of-staff",
        "model": {
            "provider": model.get("provider", ""),
            "default": model.get("default", ""),
            "temperature": model.get("temperature"),
        },
        "toolsets": sorted([toolset for toolset in data.get("toolsets", []) if toolset in SAFE_TOOLSETS]),
        "agent": {
            "max_turns": agent.get("max_turns"),
            "tool_use_enforcement": agent.get("tool_use_enforcement"),
            "task_completion_guidance": agent.get("task_completion_guidance"),
            "environment_probe": agent.get("environment_probe"),
            "gateway_timeout": agent.get("gateway_timeout"),
            "gateway_timeout_warning": agent.get("gateway_timeout_warning"),
            "clarify_timeout": agent.get("clarify_timeout"),
            "reasoning_effort": agent.get("reasoning_effort"),
        },
        "terminal": {
            "backend": terminal.get("backend"),
            "cwd": terminal.get("cwd"),
            "timeout": terminal.get("timeout"),
            "persistent_shell": terminal.get("persistent_shell"),
            "auto_source_bashrc": terminal.get("auto_source_bashrc"),
        },
        "web": {
            "backend": web.get("backend"),
            "search_backend": web.get("search_backend"),
            "extract_backend": web.get("extract_backend"),
        },
        "browser": {
            "engine": browser.get("engine"),
            "allow_private_urls": browser.get("allow_private_urls"),
            "auto_local_for_private_urls": browser.get("auto_local_for_private_urls"),
            "inactivity_timeout": browser.get("inactivity_timeout"),
            "command_timeout": browser.get("command_timeout"),
            "dialog_policy": browser.get("dialog_policy"),
            "dialog_timeout_s": browser.get("dialog_timeout_s"),
        },
        "compression": {
            "enabled": compression.get("enabled"),
            "threshold": compression.get("threshold"),
            "target_ratio": compression.get("target_ratio"),
            "protect_last_n": compression.get("protect_last_n"),
            "protect_first_n": compression.get("protect_first_n"),
        },
        "auxiliary": {},
    }

    for name in ["vision", "web_extract", "compression", "skills_hub", "approval", "mcp", "title_generation", "triage_specifier"]:
        section = auxiliary.get(name, {}) or {}
        out["auxiliary"][name] = {
            "provider": section.get("provider", ""),
            "model": section.get("model", ""),
            "timeout": section.get("timeout"),
        }

    return out


def write_yaml(path: Path, data: dict, apply: bool) -> None:
    print(f"[{'apply' if apply else 'dry-run'}] generate {path}")
    if apply:
        ensure_parent(path, apply=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    workspace = Path(args.source_workspace).resolve()
    profile = Path(args.source_profile).resolve()

    copies = [
        (workspace / "tools/headroom_phase1/hr_index_artifact.py", repo_root / "tools/headroom_phase1/hr_index_artifact.py"),
        (workspace / "tools/headroom_phase1/hr_kag_query.py", repo_root / "tools/headroom_phase1/hr_kag_query.py"),
        (workspace / "tools/headroom_phase1/hr_selective_retrieval.py", repo_root / "tools/headroom_phase1/hr_selective_retrieval.py"),
        (workspace / "tools/headroom_phase1/hr_manual_wrapper.py", repo_root / "tools/headroom_phase1/hr_manual_wrapper.py"),
        (workspace / "tools/headroom_phase1/tests/test_hr_index_artifact.py", repo_root / "tools/headroom_phase1/tests/test_hr_index_artifact.py"),
        (workspace / "tools/headroom_phase1/tests/test_hr_kag_query.py", repo_root / "tools/headroom_phase1/tests/test_hr_kag_query.py"),
        (workspace / "tools/headroom_phase1/tests/test_hr_selective_retrieval.py", repo_root / "tools/headroom_phase1/tests/test_hr_selective_retrieval.py"),
        (workspace / "tools/headroom_phase1/tests/test_hr_manual_wrapper.py", repo_root / "tools/headroom_phase1/tests/test_hr_manual_wrapper.py"),
    ]

    for src, dst in copies:
        if not src.exists():
            raise SystemExit(f"missing expected source file: {src}")
        copy_file(src, dst, apply=args.apply)

    public_config = sanitize_config(profile / "config.yaml")
    write_yaml(repo_root / "config/chief-of-staff.public.yaml", public_config, apply=args.apply)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

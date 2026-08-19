#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_SKILLS = [
    "miniciso-kag-finding-gate",
    "miniciso-headroom-phase1",
    "miniciso-institutional-learning",
]


def _require_contains(path: Path, needle: str, message: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        raise ValueError(message)


def validate_repo(repo_root: Path) -> None:
    repo_root = Path(repo_root)

    for skill in REQUIRED_SKILLS:
        skill_path = repo_root / "skills" / "security" / skill / "SKILL.md"
        if not skill_path.is_file():
            raise ValueError(f"missing bundled skill file: {skill_path}")

    soul_path = repo_root / "profiles" / "chief-of-staff" / "SOUL.md"
    if not soul_path.is_file():
        raise ValueError(f"missing SOUL.md: {soul_path}")
    for skill in REQUIRED_SKILLS:
        _require_contains(soul_path, skill, f"SOUL.md missing bundled skill reference: {skill}")
    _require_contains(soul_path, "security-qa", "SOUL.md missing security-qa gate reference")

    bootstrap_sh = repo_root / "scripts" / "bootstrap.sh"
    _require_contains(bootstrap_sh, 'skills_source="$REPO_ROOT/skills"', "bootstrap.sh missing skills source reference")
    _require_contains(bootstrap_sh, 'chief-of-staff/skills', "bootstrap.sh missing chief-of-staff skills install path")

    bootstrap_ps1 = repo_root / "scripts" / "bootstrap.ps1"
    _require_contains(bootstrap_ps1, "Join-Path $repoRoot 'skills'", "bootstrap.ps1 missing skills source reference")
    _require_contains(bootstrap_ps1, "chief-of-staff\\skills", "bootstrap.ps1 missing chief-of-staff skills install path")

    sync_sh = repo_root / "scripts" / "sync_to_hermes.sh"
    _require_contains(sync_sh, 'profiles/chief-of-staff/skills/$rel_path', "sync_to_hermes.sh missing chief-of-staff skills sync path")

    manifest_path = repo_root / "meta" / "MANIFEST.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing MANIFEST.json: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundled = manifest.get("bundled_skills")
    if bundled != REQUIRED_SKILLS:
        raise ValueError(f"MANIFEST.json bundled_skills mismatch: {bundled!r}")


def main() -> int:
    validate_repo(Path(__file__).resolve().parents[1])
    print("OK: bundled capabilities are distributed and wired into chief-of-staff runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

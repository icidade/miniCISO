import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_bundled_capabilities import validate_repo


REQUIRED_SKILLS = [
    "miniciso-kag-finding-gate",
    "miniciso-headroom-phase1",
    "miniciso-institutional-learning",
]


class BundledCapabilitiesValidationTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="miniciso-capabilities-"))
        for skill in REQUIRED_SKILLS:
            skill_dir = root / "skills" / "security" / skill
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill}\ndescription: test\n---\n\n# {skill}\n",
                encoding="utf-8",
            )

        (root / "profiles" / "chief-of-staff").mkdir(parents=True, exist_ok=True)
        (root / "profiles" / "chief-of-staff" / "SOUL.md").write_text(
            "\n".join(
                [
                    "# SOUL",
                    "miniciso-kag-finding-gate",
                    "miniciso-headroom-phase1",
                    "miniciso-institutional-learning",
                    "security-qa",
                ]
            ),
            encoding="utf-8",
        )

        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "bootstrap.sh").write_text(
            'skills_source="$REPO_ROOT/skills"\nchief_skills_root="$profile_root/chief-of-staff/skills"\n',
            encoding="utf-8",
        )
        (scripts_dir / "bootstrap.ps1").write_text(
            "$skillsSource = Join-Path $repoRoot 'skills'\n$chiefSkillsRoot = Join-Path $profileRoot 'chief-of-staff\\skills'\n",
            encoding="utf-8",
        )
        (scripts_dir / "sync_to_hermes.sh").write_text(
            'copy_file "$skill_file" "$TARGET_ROOT/profiles/chief-of-staff/skills/$rel_path"\n',
            encoding="utf-8",
        )

        meta_dir = root / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "MANIFEST.json").write_text(
            json.dumps({"bundled_skills": REQUIRED_SKILLS}, indent=2),
            encoding="utf-8",
        )
        return root

    def test_validate_repo_accepts_expected_layout(self):
        repo = self.make_repo()
        validate_repo(repo)

    def test_validate_repo_rejects_missing_skill(self):
        repo = self.make_repo()
        missing = repo / "skills" / "security" / "miniciso-headroom-phase1" / "SKILL.md"
        missing.unlink()

        with self.assertRaisesRegex(ValueError, "missing bundled skill file"):
            validate_repo(repo)

    def test_validate_repo_rejects_missing_soul_reference(self):
        repo = self.make_repo()
        soul_path = repo / "profiles" / "chief-of-staff" / "SOUL.md"
        soul_path.write_text("# SOUL\nsecurity-qa\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "SOUL.md missing bundled skill reference"):
            validate_repo(repo)

    def test_validate_repo_rejects_missing_bootstrap_install_reference(self):
        repo = self.make_repo()
        bootstrap_path = repo / "scripts" / "bootstrap.sh"
        bootstrap_path.write_text("# missing install\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "bootstrap.sh missing skills source reference"):
            validate_repo(repo)


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REPOSITORY = "https://github.com/icidade/hermes-agent.git"
EXPECTED_COMMIT = "489c6f2103ccca0ac1fc4f6249c71924ec8f024c"


def parse_env_file(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def test_runtime_pin_is_the_fork_sha_and_has_installer_hashes():
    values = parse_env_file(REPO_ROOT / "config/hermes-version.env")
    assert values["HERMES_REPOSITORY"] == EXPECTED_REPOSITORY
    assert values["HERMES_COMMIT"] == EXPECTED_COMMIT
    assert len(values["HERMES_INSTALL_SH_SHA256"]) == 64
    assert len(values["HERMES_INSTALL_PS1_SHA256"]) == 64


class RuntimePinBootstrapConfigTests(unittest.TestCase):
    def test_runtime_pin_is_the_fork_sha_and_has_installer_hashes(self):
        values = parse_env_file(REPO_ROOT / "config/hermes-version.env")
        self.assertEqual(values["HERMES_REPOSITORY"], EXPECTED_REPOSITORY)
        self.assertEqual(values["HERMES_COMMIT"], EXPECTED_COMMIT)
        self.assertEqual(len(values["HERMES_INSTALL_SH_SHA256"]), 64)
        self.assertEqual(len(values["HERMES_INSTALL_PS1_SHA256"]), 64)

    def test_bootstraps_have_no_obsolete_patchset_or_global_fallback(self):
        for bootstrap in ("scripts/bootstrap.sh", "scripts/bootstrap.ps1"):
            with self.subTest(bootstrap=bootstrap):
                text = (REPO_ROOT / bootstrap).read_text(encoding="utf-8-sig")
                self.assertNotIn("apply_hermes_patchset", text)
                self.assertNotIn(".miniciso-governance-patch.json", text)
                self.assertNotIn("git apply", text)
                self.assertNotIn("NousResearch/hermes-agent", text)
                self.assertNotIn("command -v hermes", text)
                self.assertNotIn("Get-Command hermes", text)


    def test_governance_merge_is_idempotent_and_preserves_keys(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "source.yaml"
            target = tmp_path / "chief-of-staff" / "config.yaml"
            target.parent.mkdir()
            source.write_text(
                "cost_context_governance:\n  mode: enforce\n  workspace_dir: engagements\n",
                encoding="utf-8",
            )
            target.write_text(
                "model:\n  name: local\ncustom_key: preserved\n",
                encoding="utf-8",
            )

            script = REPO_ROOT / "scripts/install_governance_config.py"
            command = [
                "python3",
                str(script),
                "--source",
                str(source),
                "--profile-config",
                str(target),
            ]
            first = subprocess.run(command, check=True, capture_output=True, text=True)
            first_bytes = target.read_bytes()
            second = subprocess.run(command, check=True, capture_output=True, text=True)

            self.assertTrue(first.stdout)
            self.assertTrue(second.stdout)
            self.assertEqual(target.read_bytes(), first_bytes)
            text = target.read_text(encoding="utf-8")
            self.assertIn("custom_key: preserved", text)
            self.assertIn("mode: enforce", text)


    def test_governance_merge_does_not_touch_other_profiles(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            chief = tmp_path / "chief-of-staff" / "config.yaml"
            chief.parent.mkdir()
            other = tmp_path / "other-profile" / "config.yaml"
            other.parent.mkdir()
            chief.write_text("existing: chief\n", encoding="utf-8")
            other.write_text("existing: other\n", encoding="utf-8")
            source = tmp_path / "source.yaml"
            source.write_text("cost_context_governance:\n  mode: enforce\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts/install_governance_config.py"),
                    "--source",
                    str(source),
                    "--profile-config",
                    str(chief),
                ],
                check=True,
            )

            self.assertIn("cost_context_governance", chief.read_text(encoding="utf-8"))
            self.assertEqual(other.read_text(encoding="utf-8"), "existing: other\n")


    def test_profile_checks_are_exact_not_substring(self):
        for path in (REPO_ROOT / "scripts/smoke-test.sh", REPO_ROOT / "scripts/smoke-test.ps1"):
            text = path.read_text(encoding="utf-8-sig")
            self.assertIn("profile list", text)
            self.assertTrue("exact" in text.lower() or "-eq" in text or "Compare-Object" in text)

    def test_skip_install_rejects_wrong_head_before_overlay_writes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "hermes-home"
            runtime = home / "hermes-agent"
            runtime.mkdir(parents=True)
            subprocess.run(["git", "-C", str(runtime), "init", "-q"], check=True)
            (runtime / "marker").write_text("wrong\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(runtime), "add", "marker"], check=True)
            subprocess.run(["git", "-C", str(runtime), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "wrong"], check=True)
            subprocess.run(["git", "-C", str(runtime), "remote", "add", "origin", EXPECTED_REPOSITORY], check=True)
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "scripts/bootstrap.sh"), "--skip-hermes-install", "--skip-provider-setup"],
                env={**os.environ, "HERMES_HOME": str(home), "MINICISO_WORKSPACE_ROOT": str(Path(directory) / "workspace")},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("HEAD does not match configured commit", result.stderr)
            self.assertFalse((home / "profiles").exists())

    def test_provenance_contract_rejects_global_executable_and_external_modules(self):
        bootstrap = (REPO_ROOT / "scripts/bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn("runtime_dir/venv/bin/hermes", bootstrap)
        self.assertIn("runtime_dir/venv/bin/python", bootstrap)
        self.assertIn("Hermes module outside governed checkout", bootstrap)
        self.assertIn("Hermes sys.path selects another checkout", bootstrap)
        self.assertIn("origin does not match configured repository", bootstrap)


if __name__ == "__main__":
    unittest.main()

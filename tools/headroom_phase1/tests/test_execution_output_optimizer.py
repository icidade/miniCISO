import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution_output_optimizer import DEFAULT_ALLOWLIST, optimize_output, load_optimizer_config


class ExecutionOutputOptimizerTests(unittest.TestCase):
    def test_default_config_is_enabled_shadow_and_uses_mvp_allowlist(self):
        config = load_optimizer_config({})
        self.assertTrue(config.enabled)
        self.assertEqual(config.mode, "shadow")
        self.assertEqual(config.allowlist, DEFAULT_ALLOWLIST)

    def test_shadow_mode_keeps_raw_output_authoritative(self):
        raw = "On branch main\nmodified: file_a.py\nmodified: file_b.py\n"
        result = optimize_output("git_status", raw, {})

        self.assertTrue(result.optimizer_applied)
        self.assertEqual(result.delivered_output, raw)
        self.assertEqual(result.authoritative_raw_output, raw)
        self.assertIsNotNone(result.reduced_output)
        assert result.reduced_output is not None
        reduced = json.loads(result.reduced_output)
        self.assertEqual(reduced["kind"], "git_status")
        self.assertEqual(reduced["modified"], 2)

    def test_kill_switch_restores_passthrough(self):
        raw = "a\nb\nc\n"
        result = optimize_output("ls", raw, {"MINICISO_EXECUTION_OUTPUT_OPTIMIZER": "0"})

        self.assertFalse(result.optimizer_applied)
        self.assertEqual(result.delivered_output, raw)
        self.assertIsNone(result.reduced_output)
        self.assertEqual(result.reason, "kill_switch_disabled")

    def test_excluded_classes_never_optimize(self):
        raw = "critical evidence"
        for operation_class in ("read_file", "sarif", "security_qa_response"):
            with self.subTest(operation_class=operation_class):
                result = optimize_output(operation_class, raw, {})
                self.assertFalse(result.optimizer_applied)
                self.assertEqual(result.delivered_output, raw)
                self.assertIsNone(result.reduced_output)
                self.assertEqual(result.reason, "excluded_operation_class")

    def test_allowlist_can_narrow_supported_classes(self):
        raw = "file1\nfile2\nfile3\n"
        env = {"MINICISO_EXECUTION_OUTPUT_OPTIMIZER_ALLOWLIST": "git_status"}

        denied = optimize_output("ls", raw, env)
        allowed = optimize_output("git_status", raw, env)

        self.assertFalse(denied.optimizer_applied)
        self.assertEqual(denied.reason, "not_allowlisted")
        self.assertTrue(allowed.optimizer_applied)

    def test_listing_preview_truncates_large_output(self):
        raw = "\n".join(f"path-{i}" for i in range(40))
        result = optimize_output("find", raw, {})
        assert result.reduced_output is not None
        reduced = json.loads(result.reduced_output)

        self.assertEqual(reduced["kind"], "find")
        self.assertEqual(reduced["line_count"], 40)
        self.assertIn("omitted", reduced["preview"])


if __name__ == "__main__":
    unittest.main()

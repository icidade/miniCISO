import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_manual_wrapper import build_selection_metadata, main


class BuildSelectionMetadataTests(unittest.TestCase):
    def test_build_selection_metadata_reads_query_index_and_pack_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            index_path = tmp / "artifact.index.json"
            query_path = tmp / "actions-release.query.json"
            pack_path = tmp / "actions-release.pack.json"

            index_path.write_text(
                json.dumps(
                    {
                        "source": {"path": "/tmp/raw.json", "sha256": "abc123", "bytes": 1234},
                        "summary": {"root_type": "dict", "node_count": 42},
                        "nodes": [],
                    }
                ),
                encoding="utf-8",
            )
            query_path.write_text(
                json.dumps(
                    {
                        "surface": "github-actions",
                        "boundary": "release-pipeline",
                        "token_budget": 12000,
                        "required_evidence_types": ["workflow triggers", "permissions"],
                    }
                ),
                encoding="utf-8",
            )
            pack_path.write_text(
                json.dumps(
                    {
                        "selected_slices": [
                            {"json_path": "workflows.release", "estimated_tokens": 500, "reason_selected": ["signal:keyword:workflow"]},
                            {"json_path": "workflows.release.permissions", "estimated_tokens": 100, "reason_selected": ["required:permission"]},
                        ],
                        "selection_metrics": {
                            "source_tokens_estimated": 5000,
                            "selected_tokens_estimated": 600,
                            "selection_saved_tokens": 4400,
                            "selection_ratio": 0.12,
                        },
                    }
                ),
                encoding="utf-8",
            )

            metadata = build_selection_metadata(index_path=index_path, query_path=query_path, pack_path=pack_path)

            self.assertTrue(metadata["enabled"])
            self.assertEqual(metadata["mode"], "shadow")
            self.assertEqual(metadata["surface"], "github-actions")
            self.assertEqual(metadata["boundary"], "release-pipeline")
            self.assertEqual(metadata["source_sha256"], "abc123")
            self.assertEqual(metadata["index_summary"]["node_count"], 42)
            self.assertEqual(metadata["selection_metrics"]["selected_tokens_estimated"], 600)
            self.assertEqual(metadata["selected_slice_count"], 2)
            self.assertEqual(
                metadata["top_selected_paths"],
                ["workflows.release", "workflows.release.permissions"],
            )
            self.assertEqual(
                metadata["top_selection_reasons"],
                ["required:permission", "signal:keyword:workflow"],
            )


class ExecutionOutputOptimizerIntegrationTests(unittest.TestCase):
    def test_wrapper_logs_shadow_derivative_but_preserves_authoritative_raw_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "ls.txt"
            output_path = tmp / "out.txt"
            log_dir = tmp / "logs"
            raw_output = "\n".join(f"file_{i}" for i in range(40)) + "\n"
            input_path.write_text(raw_output, encoding="utf-8")

            argv = [
                "hr_manual_wrapper.py",
                str(input_path),
                str(output_path),
                "--log-dir",
                str(log_dir),
                "--artifact-type",
                "command-output",
                "--execution-operation-class",
                "ls",
            ]
            env = os.environ.copy()
            env["MINICISO_HEADROOM_ENABLED"] = "0"
            env["MINICISO_EXECUTION_OUTPUT_OPTIMIZER"] = "1"
            env["MINICISO_EXECUTION_OUTPUT_OPTIMIZER_MODE"] = "shadow"

            with patch.object(sys, "argv", argv), patch.dict(os.environ, env, clear=True):
                rc = main()

            self.assertEqual(rc, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), raw_output)

            run_files = sorted(log_dir.glob("*.json"))
            self.assertEqual(len(run_files), 1)
            record = json.loads(run_files[0].read_text(encoding="utf-8"))
            optimizer = record["execution_output_optimizer"]
            self.assertTrue(optimizer["enabled"])
            self.assertTrue(optimizer["optimizer_applied"])
            self.assertEqual(optimizer["reason"], "shadow_derivative_only")
            self.assertEqual(optimizer["authoritative_raw_output"], raw_output)
            self.assertIn('"kind": "ls"', optimizer["reduced_output"])
            self.assertEqual(record["compressed"]["chars"], len(raw_output))


if __name__ == "__main__":
    unittest.main()

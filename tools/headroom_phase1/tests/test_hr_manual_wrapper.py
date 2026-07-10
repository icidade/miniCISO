import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_manual_wrapper import build_selection_metadata


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


if __name__ == "__main__":
    unittest.main()

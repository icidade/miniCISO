import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_index_artifact import build_index


class BuildIndexTests(unittest.TestCase):
    def test_build_index_emits_paths_keywords_and_ancestry(self):
        sample = {
            "workflows": {
                "release_pipeline": {
                    "permissions": {"contents": "write"},
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v4"},
                        {"name": "Publish", "run": "npm publish", "env": {"TOKEN": "${{ secrets.NPM_TOKEN }}"}},
                    ],
                }
            },
            "docs": {"summary": "General documentation"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "sample.json"
            source.write_text(json.dumps(sample), encoding="utf-8")

            result = build_index(source)

        self.assertEqual(result["source"]["path"], str(source.resolve()))
        self.assertEqual(result["summary"]["root_type"], "dict")
        self.assertGreater(result["summary"]["node_count"], 0)

        by_path = {node["json_path"]: node for node in result["nodes"]}

        self.assertIn("workflows.release_pipeline.permissions", by_path)
        self.assertIn("workflows.release_pipeline.steps[1]", by_path)
        self.assertIn("docs.summary", by_path)

        publish_step = by_path["workflows.release_pipeline.steps[1]"]
        self.assertEqual(publish_step["node_type"], "dict")
        self.assertEqual(publish_step["parent_path"], "workflows.release_pipeline.steps")
        self.assertIn("workflows.release_pipeline.steps", publish_step["ancestors"])
        self.assertIn("keyword:publish", publish_step["signals"])
        self.assertIn("keyword:secret", publish_step["signals"])
        self.assertIn("npm publish", publish_step["content_preview"])
        self.assertGreater(publish_step["estimated_tokens"], 0)

        permissions = by_path["workflows.release_pipeline.permissions"]
        self.assertIn("keyword:permission", permissions["signals"])

        docs_summary = by_path["docs.summary"]
        self.assertEqual(docs_summary["node_type"], "scalar")
        self.assertEqual(docs_summary["ancestors"], ["docs"])


if __name__ == "__main__":
    unittest.main()

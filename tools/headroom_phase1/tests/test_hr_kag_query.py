import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_kag_query import build_query


class BuildQueryTests(unittest.TestCase):
    def test_build_query_normalizes_surface_and_required_evidence(self):
        query = build_query(
            surface="github-actions",
            question="Can untrusted pull request input reach a privileged publish workflow?",
            impact_target="supply-chain / privilege boundary",
            token_budget=12000,
            anti_goals=["general CI quality", "formatting jobs"],
            required_evidence_types=["workflow triggers", "permissions", "secret usage"],
            confidence_threshold="medium",
            raw_expansion_policy="expand_on_missing_required_evidence",
        )

        self.assertEqual(query["surface"], "github-actions")
        self.assertEqual(query["token_budget"], 12000)
        self.assertEqual(query["confidence_threshold"], "medium")
        self.assertEqual(query["raw_expansion_policy"], "expand_on_missing_required_evidence")
        self.assertIn("workflow triggers", query["required_evidence_types"])
        self.assertIn("permissions", query["required_evidence_types"])
        self.assertIn("actions", query["tags"])
        self.assertIn("release", query["tags"])
        self.assertIn("publish", query["tags"])


if __name__ == "__main__":
    unittest.main()

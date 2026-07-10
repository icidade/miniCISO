import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hr_selective_retrieval import build_retrieval_pack


class BuildRetrievalPackTests(unittest.TestCase):
    def test_build_retrieval_pack_ranks_relevant_slices_within_budget(self):
        index_doc = {
            "source": {
                "path": "/tmp/source.json",
                "sha256": "abc123",
                "bytes": 1000,
            },
            "summary": {"root_type": "dict", "node_count": 4},
            "nodes": [
                {
                    "json_path": "workflows.release.permissions",
                    "node_type": "dict",
                    "ancestors": ["workflows.release"],
                    "estimated_tokens": 120,
                    "signals": ["keyword:permission", "keyword:workflow"],
                    "content_preview": "permissions: write-all",
                },
                {
                    "json_path": "workflows.release.steps[1]",
                    "node_type": "dict",
                    "ancestors": ["workflows.release.steps", "workflows.release"],
                    "estimated_tokens": 180,
                    "signals": ["keyword:publish", "keyword:secret", "keyword:workflow"],
                    "content_preview": "npm publish using secret token",
                },
                {
                    "json_path": "docs.summary",
                    "node_type": "scalar",
                    "ancestors": ["docs"],
                    "estimated_tokens": 90,
                    "signals": [],
                    "content_preview": "general documentation overview",
                },
            ],
        }
        query = {
            "surface": "github-actions",
            "question": "Can untrusted input reach a privileged publish workflow?",
            "target_claim": "publish workflow boundary",
            "impact_target": "supply-chain / privilege boundary",
            "anti_goals": ["general documentation"],
            "required_evidence_types": ["permissions", "publish commands", "secret usage"],
            "token_budget": 250,
            "confidence_threshold": "medium",
            "raw_expansion_policy": "expand_on_missing_required_evidence",
            "tags": ["actions", "publish", "release", "workflow", "permission", "secret"],
        }

        pack = build_retrieval_pack(index_doc, query)

        self.assertEqual(pack["source"]["path"], "/tmp/source.json")
        self.assertLessEqual(pack["selection_metrics"]["selected_tokens_estimated"], 250)
        self.assertGreater(pack["selection_metrics"]["selection_saved_tokens"], 0)
        self.assertEqual(len(pack["selected_slices"]), 1)
        selected = pack["selected_slices"][0]
        self.assertEqual(selected["json_path"], "workflows.release.steps[1]")
        self.assertIn("signal:keyword:publish", selected["reason_selected"])
        self.assertIn("signal:keyword:secret", selected["reason_selected"])
        self.assertEqual(pack["fallback"]["raw_required_for_final_claims"], True)

    def test_build_retrieval_pack_penalizes_sbom_name_noise_for_auth_session(self):
        index_doc = {
            "source": {
                "path": "/tmp/source.json",
                "sha256": "abc123",
                "bytes": 1000,
            },
            "summary": {"root_type": "dict", "node_count": 3},
            "nodes": [
                {
                    "json_path": "dependency_graph_sbom.data.sbom.packages[12].name",
                    "node_type": "scalar",
                    "ancestors": ["dependency_graph_sbom.data.sbom.packages[12]"],
                    "estimated_tokens": 2,
                    "signals": ["keyword:auth"],
                    "content_preview": "oauthlib",
                },
                {
                    "json_path": "auth_handlers.session_middleware",
                    "node_type": "dict",
                    "ancestors": ["auth_handlers"],
                    "estimated_tokens": 140,
                    "signals": ["keyword:auth", "keyword:session", "keyword:permission"],
                    "content_preview": "session middleware validates auth token and permission checks",
                },
            ],
        }
        query = {
            "surface": "auth-session",
            "question": "Find authorization-relevant session handling.",
            "target_claim": "authorization boundary",
            "impact_target": "authorization / session boundary",
            "anti_goals": [],
            "required_evidence_types": ["auth handlers", "session state", "permission checks"],
            "token_budget": 200,
            "confidence_threshold": "medium",
            "raw_expansion_policy": "expand_on_missing_required_evidence",
            "tags": ["auth", "session", "permission"],
        }

        pack = build_retrieval_pack(index_doc, query)

        selected_paths = [slice_["json_path"] for slice_ in pack["selected_slices"]]
        self.assertEqual(pack["selected_slices"][0]["json_path"], "auth_handlers.session_middleware")
        self.assertNotIn("dependency_graph_sbom.data.sbom.packages[12].name", selected_paths)


if __name__ == "__main__":
    unittest.main()

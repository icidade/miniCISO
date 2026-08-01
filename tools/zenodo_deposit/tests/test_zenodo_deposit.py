from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.zenodo_deposit import zenodo_deposit as zd
from tools.zenodo_deposit import update_whitepaper_frontmatter as frontmatter


def valid_metadata() -> dict:
    return {
        "title": "Test report",
        "upload_type": "publication",
        "publication_type": "report",
        "description": "A sufficiently clear test description.",
        "creators": [{"name": "Doe, Jane"}],
        "publication_date": "2026-07-10",
        "version": "1.0",
        "language": "eng",
        "license": "cc-by-4.0",
        "keywords": ["security"],
        "related_identifiers": [
            {
                "identifier": "https://github.com/example/project",
                "relation": "documents",
                "resource_type": "software",
            }
        ],
        "references": ["Doe J. Test reference."],
        "prereserve_doi": True,
    }


def local_file(name: str = "paper.pdf", content: bytes = b"%PDF-test") -> dict:
    return {
        "name": name,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "md5": hashlib.md5(content, usedforsecurity=False).hexdigest(),
    }


def draft_for(metadata: dict | None = None, file_info: dict | None = None) -> dict:
    files = []
    if file_info:
        files.append(
            {
                "filename": file_info["name"],
                "filesize": file_info["size"],
                "checksum": file_info["md5"],
            }
        )
    remote_metadata = dict(metadata or valid_metadata())
    remote_metadata["prereserve_doi"] = {
        "doi": "10.5072/zenodo.123",
        "recid": 123,
    }
    return {
        "id": 123,
        "state": "inprogress",
        "submitted": False,
        "metadata": remote_metadata,
        "files": files,
        "links": {
            "self": "https://sandbox.zenodo.org/api/deposit/depositions/123",
            "bucket": "https://sandbox.zenodo.org/api/files/bucket-id",
            "html": "https://sandbox.zenodo.org/deposit/123",
            "publish": "https://sandbox.zenodo.org/api/deposit/depositions/123/actions/publish",
        },
    }


class FakeTransport:
    def __init__(self, responses: list[zd.HttpResponse] | None = None):
        self.responses = list(responses or [])
        self.requests: list[tuple] = []
        self.uploads: list[tuple] = []

    def request(self, method, url, headers, body, timeout):
        self.requests.append((method, url, headers, body, timeout))
        return self.responses.pop(0)

    def upload_file(self, url, headers, path, timeout):
        self.uploads.append((url, headers, path, timeout))
        return self.responses.pop(0)


class MetadataValidationTests(unittest.TestCase):
    def test_valid_metadata(self):
        self.assertEqual([], zd.validate_metadata(valid_metadata()))

    def test_required_fields_and_todo_license_are_blocking(self):
        metadata = valid_metadata()
        metadata.pop("description")
        metadata["license"] = "TODO: choose"
        errors = zd.validate_metadata(metadata)
        self.assertIn("metadata.description is required", errors)
        self.assertIn("metadata.license still contains a TODO", errors)

    def test_creator_format_orcid_relation_and_prereserve(self):
        metadata = valid_metadata()
        metadata["creators"] = [{"name": "Jane Doe", "orcid": "bad"}]
        metadata["related_identifiers"][0]["relation"] = "madeUp"
        metadata["prereserve_doi"] = False
        errors = zd.validate_metadata(metadata)
        self.assertTrue(any("Family name" in item for item in errors))
        self.assertTrue(any("orcid is invalid" in item for item in errors))
        self.assertTrue(any("relation is unsupported" in item for item in errors))
        self.assertTrue(any("prereserve_doi must be true" in item for item in errors))

    def test_pdf_signature_and_sha256(self):
        content = b"%PDF-1.7\nbody"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "paper.pdf"
            path.write_bytes(content)
            result = zd.file_hashes(path)
        self.assertEqual(hashlib.sha256(content).hexdigest(), result["sha256"])
        self.assertEqual(len(content), result["size"])

    def test_invalid_pdf_signature(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "paper.pdf"
            path.write_bytes(b"not a PDF")
            with self.assertRaisesRegex(zd.ToolError, "%PDF"):
                zd.file_hashes(path)

    def test_remote_derived_metadata_fields_are_ignored_but_real_changes_are_not(self):
        local = valid_metadata()
        remote = json.loads(json.dumps(local))
        remote["creators"][0]["affiliation"] = None
        remote["related_identifiers"][0]["scheme"] = "url"
        remote["prereserve_doi"] = {"doi": "10.5072/zenodo.123", "recid": 123}
        self.assertEqual([], zd.metadata_differences(local, remote))
        remote["creators"][0]["name"] = "Doe, Janet"
        self.assertIn(
            "creators: local and remote values differ",
            zd.metadata_differences(local, remote),
        )


class FrontmatterUpdateTests(unittest.TestCase):
    XML = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:sz w:val="19"/></w:rPr><w:t xml:space="preserve">Based on miniCISO</w:t></w:r></w:p>
    <w:p><w:r><w:br w:type="page"/></w:r></w:p>
    <w:p><w:r><w:t>Executive Summary</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>'''

    def test_adds_license_before_page_break_without_rewriting_existing_xml(self):
        updated = frontmatter.update_document_xml(self.XML)
        self.assertIn(frontmatter.LICENSE_TEXT.encode(), updated)
        self.assertLess(updated.index(frontmatter.LICENSE_TEXT.encode()), updated.index(b'w:type="page"'))
        license_match = __import__("re").search(
            rb'<w:p\b[^>]*>(?:(?!</w:p>).)*Licensed under Creative Commons(?:(?!</w:p>).)*</w:p>',
            updated,
            __import__("re").DOTALL,
        )
        self.assertIsNotNone(license_match)
        restored = updated[: license_match.start()] + updated[license_match.end() :]
        self.assertEqual(self.XML, restored)

    def test_adds_and_updates_reserved_doi_idempotently(self):
        first = frontmatter.update_document_xml(self.XML, "10.5281/zenodo.123")
        second = frontmatter.update_document_xml(first, "10.5281/zenodo.456")
        self.assertEqual(1, second.count(frontmatter.LICENSE_TEXT.encode()))
        self.assertNotIn(b"zenodo.123", second)
        self.assertIn(b"DOI: 10.5281/zenodo.456", second)

    def test_rejects_invalid_doi(self):
        with self.assertRaisesRegex(frontmatter.FrontmatterError, "DOI"):
            frontmatter.update_document_xml(self.XML, "https://doi.org/not-a-doi")


class EnvironmentAndSanitizationTests(unittest.TestCase):
    def test_sandbox_and_production_base_urls(self):
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "test-token"}, clear=True):
            sandbox = zd.ZenodoClient("sandbox", FakeTransport())
            production = zd.ZenodoClient("production", FakeTransport())
        self.assertEqual("https://sandbox.zenodo.org", sandbox.base_url)
        self.assertEqual("https://zenodo.org", production.base_url)

    def test_invalid_environment_and_missing_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(zd.ToolError, "sandbox.*production"):
                zd.ZenodoClient("invalid", FakeTransport())
            with self.assertRaisesRegex(zd.ToolError, "not configured"):
                zd.ZenodoClient("sandbox", FakeTransport())

    def test_token_is_header_only_and_sanitized_from_error(self):
        token = "super-secret-value"
        response = zd.HttpResponse(
            422,
            {},
            json.dumps({"message": f"bad {token} access_token={token}"}).encode(),
        )
        transport = FakeTransport([response])
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": token}, clear=True):
            client = zd.ZenodoClient("sandbox", transport)
            with self.assertRaises(zd.ApiError) as caught:
                client.request(
                    "PUT",
                    "https://sandbox.zenodo.org/api/deposit/depositions/123",
                    {"metadata": {}},
                )
        message = str(caught.exception)
        self.assertNotIn(token, message)
        method, url, headers, body, _ = transport.requests[0]
        self.assertEqual("PUT", method)
        self.assertNotIn(token, url)
        self.assertEqual(f"Bearer {token}", headers["Authorization"])
        self.assertNotIn(token.encode(), body)

    def test_foreign_or_cross_environment_link_is_refused(self):
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "token"}, clear=True):
            client = zd.ZenodoClient("sandbox", FakeTransport())
            with self.assertRaisesRegex(zd.ToolError, "outside"):
                client.request("GET", "https://zenodo.org/api/deposit/depositions/123")
            with self.assertRaisesRegex(zd.ToolError, "outside"):
                client.request(
                    "GET", "https://sandbox.zenodo.org:444/api/deposit/depositions/123"
                )
            with self.assertRaisesRegex(zd.ToolError, "outside"):
                client.request(
                    "GET", "https://user@sandbox.zenodo.org/api/deposit/depositions/123"
                )

    def test_production_mutation_needs_two_explicit_gates(self):
        with self.assertRaisesRegex(zd.ToolError, "blocked"):
            zd._production_mutation_guard("production", False, True)
        with self.assertRaisesRegex(zd.ToolError, "blocked"):
            zd._production_mutation_guard("production", True, False)
        zd._production_mutation_guard("production", True, True)
        zd._production_mutation_guard("sandbox", False, False)


class ApiReliabilityTests(unittest.TestCase):
    def test_supported_error_statuses_are_useful(self):
        for status in (401, 403, 404, 409, 415, 422):
            with self.subTest(status=status):
                transport = FakeTransport(
                    [zd.HttpResponse(status, {}, b'{"message":"test failure"}')]
                )
                with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "token"}, clear=True):
                    client = zd.ZenodoClient("sandbox", transport)
                    with self.assertRaises(zd.ApiError) as caught:
                        client.request(
                            "PUT",
                            "https://sandbox.zenodo.org/api/deposit/depositions/123",
                            {},
                        )
                self.assertEqual(status, caught.exception.status)
                self.assertIn(f"HTTP {status}", str(caught.exception))

    def test_get_retries_429_and_respects_retry_after(self):
        transport = FakeTransport(
            [
                zd.HttpResponse(429, {"Retry-After": "3"}, b'{"message":"slow down"}'),
                zd.HttpResponse(200, {}, b'{"id":123}'),
            ]
        )
        sleeps: list[float] = []
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "token"}, clear=True):
            client = zd.ZenodoClient("sandbox", transport, sleeps.append)
            result = client.get_draft(123)
        self.assertEqual(123, result["id"])
        self.assertEqual([3.0], sleeps)
        self.assertEqual(2, len(transport.requests))

    def test_safe_put_retries_5xx_but_create_post_does_not(self):
        retry_transport = FakeTransport(
            [
                zd.HttpResponse(503, {}, b'{"message":"temporary"}'),
                zd.HttpResponse(200, {}, b'{"id":123}'),
            ]
        )
        post_transport = FakeTransport(
            [zd.HttpResponse(503, {}, b'{"message":"temporary"}')]
        )
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "token"}, clear=True):
            retry_client = zd.ZenodoClient("sandbox", retry_transport, lambda _: None)
            result = retry_client.update_metadata(
                "https://sandbox.zenodo.org/api/deposit/depositions/123",
                valid_metadata(),
            )
            self.assertEqual(123, result["id"])
            post_client = zd.ZenodoClient("sandbox", post_transport, lambda _: None)
            with self.assertRaises(zd.ApiError):
                post_client.create_empty_draft()
        self.assertEqual(2, len(retry_transport.requests))
        self.assertEqual(1, len(post_transport.requests))

    def test_network_failure_reports_ambiguous_without_token(self):
        token = "never-print-this"
        transport = Mock()
        transport.request.side_effect = OSError(f"failure {token}")
        with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": token}, clear=True):
            client = zd.ZenodoClient("sandbox", transport)
            with self.assertRaises(zd.ApiError) as caught:
                client.create_empty_draft()
        self.assertIn("ambiguous", str(caught.exception))
        self.assertNotIn(token, str(caught.exception))


class StreamingUploadTests(unittest.TestCase):
    def test_client_uses_bucket_link_and_path_object(self):
        content = b"%PDF-upload"
        result = b'{"key":"paper name.pdf"}'
        transport = FakeTransport([zd.HttpResponse(200, {}, result)])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "paper name.pdf"
            path.write_bytes(content)
            with patch.dict(os.environ, {"ZENODO_ACCESS_TOKEN": "token"}, clear=True):
                client = zd.ZenodoClient("sandbox", transport)
                client.upload("https://sandbox.zenodo.org/api/files/bucket", path)
        url, headers, passed_path, timeout = transport.uploads[0]
        self.assertTrue(url.endswith("/paper%20name.pdf"))
        self.assertEqual(path, passed_path)
        self.assertNotIn("Content-Type", headers)
        self.assertEqual(zd.HTTP_TIMEOUT, timeout)

    @patch("tools.zenodo_deposit.zenodo_deposit.http.client.HTTPSConnection")
    def test_transport_streams_in_multiple_chunks(self, connection_class):
        connection = connection_class.return_value
        response = Mock()
        response.status = 200
        response.getheaders.return_value = []
        response.read.return_value = b"{}"
        connection.getresponse.return_value = response
        content = b"%PDF" + b"x" * (zd.READ_CHUNK * 2 + 10)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "large.pdf"
            path.write_bytes(content)
            result = zd.HttpTransport().upload_file(
                "https://sandbox.zenodo.org/api/files/bucket/large.pdf",
                {"Authorization": "Bearer fake"},
                path,
                30,
            )
        self.assertEqual(200, result.status)
        self.assertGreaterEqual(connection.send.call_count, 3)
        connection.putheader.assert_any_call(
            "Content-Type", "application/octet-stream"
        )
        sent_lengths = [len(call.args[0]) for call in connection.send.call_args_list]
        self.assertLessEqual(max(sent_lengths), zd.READ_CHUNK)

    def test_remote_name_size_and_checksums(self):
        info = local_file()
        draft = draft_for(file_info=info)
        self.assertEqual([], zd.verify_remote_file(draft, info))
        draft["files"][0]["filesize"] += 1
        self.assertIn("size", zd.verify_remote_file(draft, info)[0])
        draft["files"][0]["filesize"] -= 1
        draft["files"][0]["checksum"] = "md5:bad"
        self.assertIn("checksum", zd.verify_remote_file(draft, info)[0])

    def test_replacement_needs_flag_and_exact_confirmation(self):
        with self.assertRaisesRegex(zd.ToolError, "did not match"):
            zd._confirm_replace(123, "paper.pdf", lambda _: "yes")
        zd._confirm_replace(123, "paper.pdf", lambda _: "REPLACE 123 paper.pdf")


class DraftAndPublishGuardTests(unittest.TestCase):
    def test_create_draft_reuses_matching_valid_state(self):
        metadata = valid_metadata()
        draft = draft_for(metadata)
        fake_client = Mock()
        fake_client.get_draft.return_value = draft
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / ".zenodo-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "environment": "sandbox",
                        "deposition_id": 123,
                        "phase": "metadata_saved",
                        "links": {"self": draft["links"]["self"]},
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                metadata=Path("metadata.json"),
                pdf=Path("paper.pdf"),
                environment="sandbox",
                environment_explicit=False,
                allow_production=False,
                state=state_path,
            )
            with patch.object(zd, "validate_local", return_value=(metadata, local_file())), patch.object(
                zd, "ZenodoClient", return_value=fake_client
            ):
                zd.command_create_draft(args)
        fake_client.create_empty_draft.assert_not_called()
        fake_client.update_metadata.assert_not_called()

    def test_stale_state_refuses_duplicate(self):
        fake_client = Mock()
        fake_client.get_draft.side_effect = zd.ApiError(404, "missing")
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / ".zenodo-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "environment": "sandbox",
                        "deposition_id": 123,
                        "phase": "metadata_saved",
                        "links": {"self": "https://sandbox.zenodo.org/api/deposit/depositions/123"},
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                metadata=Path("metadata.json"),
                pdf=Path("paper.pdf"),
                environment="sandbox",
                environment_explicit=False,
                allow_production=False,
                state=state_path,
            )
            with patch.object(
                zd, "validate_local", return_value=(valid_metadata(), local_file())
            ), patch.object(zd, "ZenodoClient", return_value=fake_client):
                with self.assertRaisesRegex(zd.ToolError, "duplicate"):
                    zd.command_create_draft(args)
        fake_client.create_empty_draft.assert_not_called()

    def test_saved_state_with_remote_metadata_changes_refuses_overwrite(self):
        metadata = valid_metadata()
        changed = draft_for(metadata)
        changed["metadata"]["title"] = "Edited in the web UI"
        fake_client = Mock()
        fake_client.get_draft.return_value = changed
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / ".zenodo-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "environment": "sandbox",
                        "deposition_id": 123,
                        "phase": "metadata_saved",
                        "links": {"self": changed["links"]["self"]},
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                metadata=Path("metadata.json"),
                pdf=Path("paper.pdf"),
                environment="sandbox",
                environment_explicit=False,
                allow_production=False,
                state=state_path,
            )
            with patch.object(
                zd, "validate_local", return_value=(metadata, local_file())
            ), patch.object(zd, "ZenodoClient", return_value=fake_client):
                with self.assertRaisesRegex(zd.ToolError, "refusing to overwrite"):
                    zd.command_create_draft(args)
        fake_client.create_empty_draft.assert_not_called()
        fake_client.update_metadata.assert_not_called()

    def test_publish_flag_environment_id_and_ci_guards(self):
        base = argparse.Namespace(
            publish=False,
            environment="production",
            environment_explicit=True,
            deposition_id=123,
            metadata=Path("metadata.json"),
            pdf=Path("paper.pdf"),
        )
        with self.assertRaisesRegex(zd.ToolError, "--publish"):
            zd.command_publish(base)
        base.publish = True
        base.environment = "sandbox"
        with self.assertRaisesRegex(zd.ToolError, "production"):
            zd.command_publish(base)
        base.environment = "production"
        base.deposition_id = None
        with self.assertRaisesRegex(zd.ToolError, "deposition-id"):
            zd.command_publish(base)
        base.deposition_id = 123
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            with self.assertRaisesRegex(zd.ToolError, "CI"):
                zd.command_publish(base)

    def test_publish_rejects_metadata_file_and_doi_problems(self):
        metadata = valid_metadata()
        info = local_file()
        draft = draft_for(metadata, info)
        draft["metadata"]["title"] = "different"
        draft["metadata"]["prereserve_doi"] = True
        draft["files"][0]["checksum"] = "bad"
        fake_client = Mock()
        fake_client.get_draft.return_value = draft
        args = argparse.Namespace(
            publish=True,
            environment="production",
            environment_explicit=True,
            deposition_id=123,
            metadata=Path("metadata.json"),
            pdf=Path("paper.pdf"),
        )
        with patch.object(zd, "validate_local", return_value=(metadata, info)), patch.object(
            zd, "ZenodoClient", return_value=fake_client
        ), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(zd.ToolError) as caught:
                zd.command_publish(args)
        message = str(caught.exception)
        self.assertIn("title", message)
        self.assertIn("checksum", message)
        self.assertIn("reserved DOI", message)
        fake_client.publish.assert_not_called()

    def test_publish_confirmation_must_contain_exact_id(self):
        metadata = valid_metadata()
        info = local_file()
        draft = draft_for(metadata, info)
        draft["links"]["self"] = "https://zenodo.org/api/deposit/depositions/123"
        draft["links"]["bucket"] = "https://zenodo.org/api/files/bucket-id"
        draft["links"]["html"] = "https://zenodo.org/deposit/123"
        draft["links"]["publish"] = (
            "https://zenodo.org/api/deposit/depositions/123/actions/publish"
        )
        fake_client = Mock()
        fake_client.get_draft.return_value = draft
        args = argparse.Namespace(
            publish=True,
            environment="production",
            environment_explicit=True,
            deposition_id=123,
            metadata=Path("metadata.json"),
            pdf=Path("paper.pdf"),
        )
        with patch.object(zd, "validate_local", return_value=(metadata, info)), patch.object(
            zd, "ZenodoClient", return_value=fake_client
        ), patch("builtins.input", return_value="PUBLISH 999"), patch.dict(
            os.environ, {}, clear=True
        ):
            with self.assertRaisesRegex(zd.ToolError, "did not match"):
                zd.command_publish(args)
        fake_client.publish.assert_not_called()

    def test_publish_uses_only_validated_returned_link_after_exact_confirmation(self):
        metadata = valid_metadata()
        info = local_file()
        draft = draft_for(metadata, info)
        publish_url = "https://zenodo.org/api/deposit/depositions/123/actions/publish"
        for key, value in {
            "self": "https://zenodo.org/api/deposit/depositions/123",
            "bucket": "https://zenodo.org/api/files/bucket-id",
            "html": "https://zenodo.org/deposit/123",
            "publish": publish_url,
        }.items():
            draft["links"][key] = value
        fake_client = Mock()
        fake_client.get_draft.return_value = draft
        fake_client.publish.return_value = {**draft, "state": "done", "submitted": True}
        args = argparse.Namespace(
            publish=True,
            environment="production",
            environment_explicit=True,
            deposition_id=123,
            metadata=Path("metadata.json"),
            pdf=Path("paper.pdf"),
        )
        with patch.object(zd, "validate_local", return_value=(metadata, info)), patch.object(
            zd, "ZenodoClient", return_value=fake_client
        ), patch("builtins.input", return_value="PUBLISH 123"), patch.dict(
            os.environ, {}, clear=True
        ):
            zd.command_publish(args)
        fake_client.publish.assert_called_once_with(publish_url)

    def test_malformed_publish_link_is_refused(self):
        with self.assertRaisesRegex(zd.ToolError, "inconsistent"):
            zd._validate_publish_link(
                "https://sandbox.zenodo.org/api/deposit/depositions/123/actions/publish",
                123,
            )
        with self.assertRaisesRegex(zd.ToolError, "inconsistent"):
            zd._validate_publish_link(
                "https://zenodo.org/api/deposit/depositions/999/actions/publish",
                123,
            )


if __name__ == "__main__":
    unittest.main()

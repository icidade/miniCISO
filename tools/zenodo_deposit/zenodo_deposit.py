#!/usr/bin/env python3
"""Validate and manage a Zenodo draft without publishing by default."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Mapping


BASE_URLS = {
    "sandbox": "https://sandbox.zenodo.org",
    "production": "https://zenodo.org",
}
REQUIRED_METADATA = ("title", "upload_type", "description", "creators", "publication_date")
ALLOWED_UPLOAD_TYPES = {
    "publication",
    "poster",
    "presentation",
    "dataset",
    "image",
    "video",
    "software",
    "lesson",
    "physicalobject",
    "other",
}
ALLOWED_PUBLICATION_TYPES = {
    "annotationcollection",
    "book",
    "section",
    "conferencepaper",
    "datamanagementplan",
    "article",
    "patent",
    "preprint",
    "deliverable",
    "milestone",
    "proposal",
    "report",
    "softwaredocumentation",
    "taxonomictreatment",
    "technicalnote",
    "thesis",
    "workingpaper",
    "other",
}
ALLOWED_RELATIONS = {
    "isCitedBy",
    "cites",
    "isSupplementTo",
    "isSupplementedBy",
    "isContinuedBy",
    "continues",
    "isDescribedBy",
    "describes",
    "hasMetadata",
    "isMetadataFor",
    "isNewVersionOf",
    "isPreviousVersionOf",
    "isPartOf",
    "hasPart",
    "isReferencedBy",
    "references",
    "isDocumentedBy",
    "documents",
    "isCompiledBy",
    "compiles",
    "isVariantFormOf",
    "isOriginalFormof",
    "isIdenticalTo",
    "isAlternateIdentifier",
    "isReviewedBy",
    "reviews",
    "isDerivedFrom",
    "isSourceOf",
    "requires",
    "isRequiredBy",
    "isObsoletedBy",
    "obsoletes",
}
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAPER_DIR = REPO_ROOT / "docs" / "whitepapers" / "evidence-closure-loop"
DEFAULT_METADATA = DEFAULT_PAPER_DIR / "zenodo.json"
DEFAULT_PDF = DEFAULT_PAPER_DIR / "evidence-closure-loop-whitepaper.pdf"
DEFAULT_STATE = DEFAULT_PAPER_DIR / ".zenodo-state.json"
READ_CHUNK = 1024 * 1024
HTTP_TIMEOUT = 30.0
MAX_SAFE_RETRIES = 2


class ToolError(RuntimeError):
    """Expected, sanitized command failure."""


class ApiError(ToolError):
    """Sanitized Zenodo API failure."""

    def __init__(self, status: int | None, message: str):
        self.status = status
        super().__init__(message)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> Any:
        if not self.body:
            return {}
        return json.loads(self.body.decode("utf-8"))


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent Authorization headers from following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sanitize(value: object, secrets: tuple[str, ...] = ()) -> str:
    """Return printable text with known credentials and bearer values removed."""
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(access_token=)[^&\s]+", r"\1[REDACTED]", text)
    return text


def _json_error_message(body: bytes) -> str:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "The server returned a non-JSON error response."
    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("status")
        errors = payload.get("errors")
        if errors:
            return f"{message or 'Validation failed'}: {errors}"
        if message:
            return str(message)
    return "The server rejected the request."


def _status_guidance(status: int) -> str:
    return {
        401: "Authentication failed; check ZENODO_ACCESS_TOKEN and its environment.",
        403: "Permission denied; check token scopes and draft ownership.",
        404: "The requested draft or API link was not found.",
        409: "Zenodo reported a state conflict; inspect the draft before retrying.",
        415: "Zenodo rejected the media type; verify the request and PDF.",
        422: "Zenodo rejected the metadata or file validation.",
        429: "Zenodo rate-limited the request.",
    }.get(status, "Zenodo returned an API error.")


def _retry_after(headers: Mapping[str, str]) -> float | None:
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
            return max(0.0, parsed.timestamp() - time.time())
        except (TypeError, ValueError, OverflowError):
            return None


class HttpTransport:
    """Small stdlib-only HTTPS transport with streaming file upload."""

    def __init__(self):
        self._opener = urllib.request.build_opener(_NoRedirectHandler())

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HttpResponse:
        request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return HttpResponse(response.status, dict(response.headers.items()), response.read())
        except urllib.error.HTTPError as exc:
            return HttpResponse(exc.code, dict(exc.headers.items()), exc.read())

    def upload_file(
        self,
        url: str,
        headers: Mapping[str, str],
        path: Path,
        timeout: float,
    ) -> HttpResponse:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ToolError("Upload URL must be an absolute HTTPS URL.")
        target = urllib.parse.urlunsplit(("", "", parsed.path, parsed.query, ""))
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port, timeout=timeout)
        try:
            connection.putrequest("PUT", target)
            for name, value in headers.items():
                connection.putheader(name, value)
            connection.putheader("Content-Type", "application/octet-stream")
            connection.putheader("Content-Length", str(path.stat().st_size))
            connection.endheaders()
            with path.open("rb") as stream:
                while chunk := stream.read(READ_CHUNK):
                    connection.send(chunk)
            response = connection.getresponse()
            return HttpResponse(response.status, dict(response.getheaders()), response.read())
        finally:
            connection.close()


class ZenodoClient:
    def __init__(
        self,
        environment: str,
        transport: HttpTransport | Any | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if environment not in BASE_URLS:
            raise ToolError("ZENODO_ENV must be 'sandbox' or 'production'.")
        token = os.environ.get("ZENODO_ACCESS_TOKEN")
        if not token:
            raise ToolError(
                "ZENODO_ACCESS_TOKEN is not configured; no remote request was made."
            )
        self.environment = environment
        self.base_url = BASE_URLS[environment]
        self._token = token
        self._transport = transport or HttpTransport()
        self._sleeper = sleeper

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": "miniCISO-zenodo-draft-tool/1.0",
        }

    def _check_url(self, url: str) -> None:
        parsed = urllib.parse.urlsplit(url)
        expected = urllib.parse.urlsplit(self.base_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != expected.hostname
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ToolError(
                f"Refusing API link outside the selected {self.environment} Zenodo host."
            )

    def request(
        self,
        method: str,
        url: str,
        payload: Any | None = None,
        safe_retry: bool = False,
    ) -> dict[str, Any]:
        self._check_url(url)
        body = None
        headers = self._headers
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        attempts = MAX_SAFE_RETRIES + 1 if safe_retry else 1
        for attempt in range(attempts):
            try:
                response = self._transport.request(method, url, headers, body, HTTP_TIMEOUT)
            except (OSError, TimeoutError) as exc:
                raise ApiError(
                    None,
                    sanitize(
                        "Network error. The result may be ambiguous; inspect Zenodo before retrying. "
                        f"Details: {exc}",
                        (self._token,),
                    ),
                ) from None
            if 200 <= response.status < 300:
                try:
                    result = response.json()
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise ApiError(response.status, "Zenodo returned invalid JSON.") from None
                if not isinstance(result, dict):
                    raise ApiError(response.status, "Zenodo returned an unexpected response shape.")
                return result
            retryable = response.status == 429 or response.status >= 500
            if safe_retry and retryable and attempt + 1 < attempts:
                wait = _retry_after(response.headers) if response.status == 429 else 0.5 * (attempt + 1)
                if wait is not None and wait > 60:
                    raise ApiError(
                        response.status,
                        "Retry-After exceeds 60 seconds; wait as instructed and retry manually.",
                    )
                self._sleeper(wait or 0.0)
                continue
            details = sanitize(_json_error_message(response.body), (self._token,))
            raise ApiError(
                response.status,
                f"{_status_guidance(response.status)} HTTP {response.status}. {details}",
            )
        raise ApiError(None, "Request failed unexpectedly.")

    def create_empty_draft(self) -> dict[str, Any]:
        url = f"{self.base_url}/api/deposit/depositions"
        return self.request("POST", url, {})

    def get_draft(self, deposition_id: int, self_url: str | None = None) -> dict[str, Any]:
        url = self_url or f"{self.base_url}/api/deposit/depositions/{deposition_id}"
        return self.request("GET", url, safe_retry=True)

    def update_metadata(self, self_url: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return self.request("PUT", self_url, {"metadata": metadata}, safe_retry=True)

    def upload(self, bucket_url: str, pdf_path: Path) -> dict[str, Any]:
        filename = urllib.parse.quote(pdf_path.name, safe="")
        url = f"{bucket_url.rstrip('/')}/{filename}"
        self._check_url(url)
        try:
            response = self._transport.upload_file(url, self._headers, pdf_path, HTTP_TIMEOUT)
        except (OSError, TimeoutError) as exc:
            raise ApiError(
                None,
                sanitize(
                    "Upload failed and its result may be ambiguous; inspect the draft before retrying. "
                    f"Details: {exc}",
                    (self._token,),
                ),
            ) from None
        if not 200 <= response.status < 300:
            details = sanitize(_json_error_message(response.body), (self._token,))
            raise ApiError(
                response.status,
                f"{_status_guidance(response.status)} HTTP {response.status}. {details}",
            )
        try:
            result = response.json()
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(response.status, "Zenodo returned invalid JSON after upload.") from None
        if not isinstance(result, dict):
            raise ApiError(response.status, "Zenodo returned an unexpected upload response.")
        return result

    def publish(self, publish_url: str) -> dict[str, Any]:
        return self.request("POST", publish_url)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ToolError(f"File not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}.") from None
    if not isinstance(value, dict):
        raise ToolError(f"Expected a JSON object in {path}.")
    return value


def save_state(path: Path, state: dict[str, Any]) -> None:
    allowed = {
        "environment": state.get("environment"),
        "deposition_id": state.get("deposition_id"),
        "phase": state.get("phase"),
        "reserved_doi": state.get("reserved_doi"),
        "links": {
            key: value
            for key, value in (state.get("links") or {}).items()
            if key in {"self", "html", "latest_draft_html", "bucket", "publish", "files"}
        },
    }
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        json.dumps(allowed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def validate_metadata(metadata: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_METADATA:
        if field not in metadata:
            errors.append(f"metadata.{field} is required")
    for field in ("title", "description", "license"):
        value = metadata.get(field)
        if field == "license" and value is None:
            errors.append("metadata.license is required by this publication workflow")
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"metadata.{field} must be a non-empty string")
        elif "TODO" in value.upper():
            errors.append(f"metadata.{field} still contains a TODO")
    upload_type = metadata.get("upload_type")
    if upload_type not in ALLOWED_UPLOAD_TYPES:
        errors.append("metadata.upload_type is not a supported Zenodo value")
    publication_type = metadata.get("publication_type")
    if upload_type == "publication" and publication_type not in ALLOWED_PUBLICATION_TYPES:
        errors.append("metadata.publication_type is required and unsupported")
    creators = metadata.get("creators")
    if not isinstance(creators, list) or not creators:
        errors.append("metadata.creators must be a non-empty array")
    else:
        for index, creator in enumerate(creators):
            if not isinstance(creator, dict) or not isinstance(creator.get("name"), str):
                errors.append(f"metadata.creators[{index}].name is required")
            elif "," not in creator["name"]:
                errors.append(
                    f"metadata.creators[{index}].name must use 'Family name, Given names'"
                )
            orcid = creator.get("orcid") if isinstance(creator, dict) else None
            if orcid and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", str(orcid)):
                errors.append(f"metadata.creators[{index}].orcid is invalid")
    publication_date = metadata.get("publication_date")
    try:
        date.fromisoformat(publication_date)
    except (TypeError, ValueError):
        errors.append("metadata.publication_date must use YYYY-MM-DD")
    if metadata.get("prereserve_doi") is not True:
        errors.append("metadata.prereserve_doi must be true")
    for field in ("keywords", "references"):
        value = metadata.get(field)
        if value is not None and (
            not isinstance(value, list) or not all(isinstance(item, str) for item in value)
        ):
            errors.append(f"metadata.{field} must be an array of strings")
    for index, related in enumerate(metadata.get("related_identifiers", [])):
        if not isinstance(related, dict):
            errors.append(f"metadata.related_identifiers[{index}] must be an object")
            continue
        if not related.get("identifier"):
            errors.append(f"metadata.related_identifiers[{index}].identifier is required")
        if related.get("relation") not in ALLOWED_RELATIONS:
            errors.append(f"metadata.related_identifiers[{index}].relation is unsupported")
    return errors


def file_hashes(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ToolError(f"PDF not found: {path}")
    sha256 = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        signature = stream.read(4)
        if signature != b"%PDF":
            raise ToolError(f"File does not start with the %PDF signature: {path}")
        sha256.update(signature)
        md5.update(signature)
        while chunk := stream.read(READ_CHUNK):
            sha256.update(chunk)
            md5.update(chunk)
    return {"name": path.name, "size": path.stat().st_size, "sha256": sha256.hexdigest(), "md5": md5.hexdigest()}


def validate_local(metadata_path: Path, pdf_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = load_json(metadata_path)
    errors = validate_metadata(metadata)
    file_info = file_hashes(pdf_path)
    summary = {
        "title": metadata.get("title"),
        "creators": [item.get("name") for item in metadata.get("creators", []) if isinstance(item, dict)],
        "publication_date": metadata.get("publication_date"),
        "version": metadata.get("version"),
        "license": metadata.get("license"),
        "pdf": {key: file_info[key] for key in ("name", "size", "sha256")},
        "prereserve_doi": metadata.get("prereserve_doi"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if errors:
        raise ToolError("Local validation failed:\n- " + "\n- ".join(errors))
    return metadata, file_info


def _reserved_doi(draft: dict[str, Any]) -> str | None:
    value = (draft.get("metadata") or {}).get("prereserve_doi")
    if isinstance(value, dict):
        doi = value.get("doi")
        return str(doi) if doi else None
    return None


def _state_from_draft(environment: str, draft: dict[str, Any], phase: str) -> dict[str, Any]:
    return {
        "environment": environment,
        "deposition_id": draft.get("id"),
        "phase": phase,
        "reserved_doi": _reserved_doi(draft),
        "links": draft.get("links") or {},
    }


def _draft_links(draft: dict[str, Any]) -> dict[str, str]:
    links = draft.get("links")
    if not isinstance(links, dict):
        raise ToolError("Draft response has no usable links.")
    return {str(key): str(value) for key, value in links.items() if value}


def _deposition_id(value: Any) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ToolError("A numeric deposition ID is required.") from None
    if result <= 0:
        raise ToolError("A positive deposition ID is required.")
    return result


def _load_target(
    client: ZenodoClient,
    state_path: Path,
    explicit_id: int | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    state = load_json(state_path) if state_path.exists() else None
    if state and state.get("environment") != client.environment:
        raise ToolError("Local state belongs to a different Zenodo environment.")
    if explicit_id is not None:
        deposition_id = _deposition_id(explicit_id)
        if state and _deposition_id(state.get("deposition_id")) != deposition_id:
            raise ToolError("Explicit deposition ID conflicts with local state.")
    elif state:
        deposition_id = _deposition_id(state.get("deposition_id"))
    else:
        raise ToolError("No deposition ID was provided and no local state exists.")
    self_url = (state.get("links") or {}).get("self") if state else None
    return client.get_draft(deposition_id, self_url), state


def _metadata_value_matches(local: Any, remote: Any) -> bool:
    """Compare submitted metadata while allowing server-added derived fields."""
    if isinstance(local, dict):
        if not isinstance(remote, dict):
            return False
        return all(
            key in remote and _metadata_value_matches(value, remote[key])
            for key, value in local.items()
        )
    if isinstance(local, list):
        return isinstance(remote, list) and len(local) == len(remote) and all(
            _metadata_value_matches(local_item, remote_item)
            for local_item, remote_item in zip(local, remote)
        )
    return local == remote


def metadata_differences(local: dict[str, Any], remote: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    for key, local_value in local.items():
        if key == "prereserve_doi":
            if not isinstance(remote.get(key), dict):
                differences.append("prereserve_doi: DOI is not reserved remotely")
            continue
        if key not in remote or not _metadata_value_matches(local_value, remote[key]):
            differences.append(f"{key}: local and remote values differ")
    return differences


def _remote_file_info(file_item: dict[str, Any]) -> dict[str, Any]:
    checksum = file_item.get("checksum")
    if isinstance(checksum, str) and ":" in checksum:
        algorithm, checksum = checksum.split(":", 1)
    else:
        algorithm = "md5"
    return {
        "name": file_item.get("filename") or file_item.get("key"),
        "size": file_item.get("filesize") or file_item.get("size"),
        "checksum_algorithm": algorithm,
        "checksum": checksum,
    }


def verify_remote_file(draft: dict[str, Any], local: dict[str, Any]) -> list[str]:
    files = draft.get("files") or []
    matches = [
        _remote_file_info(item)
        for item in files
        if isinstance(item, dict) and _remote_file_info(item)["name"] == local["name"]
    ]
    if not matches:
        return [f"remote PDF is missing: {local['name']}"]
    if len(matches) > 1:
        return [f"multiple remote files match {local['name']}"]
    remote = matches[0]
    differences: list[str] = []
    try:
        remote_size = int(remote["size"])
    except (TypeError, ValueError):
        remote_size = None
    if remote_size is not None and remote_size != local["size"]:
        differences.append("remote PDF size differs from local PDF")
    if remote["checksum"]:
        if remote["checksum_algorithm"].lower() == "md5" and remote["checksum"].lower() != local["md5"]:
            differences.append("remote PDF MD5 checksum differs from local PDF")
        elif remote["checksum_algorithm"].lower() == "sha256" and remote["checksum"].lower() != local["sha256"]:
            differences.append("remote PDF SHA-256 checksum differs from local PDF")
    return differences


def _ensure_unpublished(draft: dict[str, Any]) -> None:
    if draft.get("submitted") is True or draft.get("state") in {"done", "published"}:
        raise ToolError("The deposition is already published and cannot be changed as a draft.")


def _production_mutation_guard(environment: str, explicit_environment: bool, allow: bool) -> None:
    if environment == "production" and not (explicit_environment and allow):
        raise ToolError(
            "Production mutation is blocked. Pass both --environment production and "
            "--allow-production after reviewing the command."
        )


def command_create_draft(args: argparse.Namespace) -> None:
    metadata, _ = validate_local(args.metadata, args.pdf)
    _production_mutation_guard(args.environment, args.environment_explicit, args.allow_production)
    client = ZenodoClient(args.environment)
    if args.state.exists():
        state = load_json(args.state)
        if state.get("environment") != args.environment:
            raise ToolError("Existing local state belongs to a different environment.")
        deposition_id = _deposition_id(state.get("deposition_id"))
        try:
            draft = client.get_draft(deposition_id, (state.get("links") or {}).get("self"))
        except ApiError as exc:
            if exc.status == 404:
                raise ToolError(
                    "Local state points to a missing draft. Refusing to create a duplicate; "
                    "resolve the ambiguity manually."
                ) from None
            raise
        _ensure_unpublished(draft)
        if state.get("phase") in {"metadata_saved", "file_verified"}:
            differences = metadata_differences(metadata, draft.get("metadata") or {})
            if differences:
                raise ToolError(
                    "Existing draft metadata changed after local state was saved. "
                    "Inspect and reconcile it manually; refusing to overwrite."
                )
            print_draft_summary(draft, "Existing draft")
            return
    else:
        draft = client.create_empty_draft()
        if not draft.get("id"):
            raise ToolError(
                "Zenodo did not return a deposition ID. Inspect your account before retrying."
            )
        save_state(args.state, _state_from_draft(args.environment, draft, "created_empty"))
    links = _draft_links(draft)
    self_url = links.get("self")
    if not self_url:
        raise ToolError("Draft response did not include a self link.")
    updated = client.update_metadata(self_url, metadata)
    save_state(args.state, _state_from_draft(args.environment, updated, "metadata_saved"))
    print_draft_summary(updated, "Draft ready")


def _confirm_replace(deposition_id: int, filename: str, input_fn: Callable[[str], str] = input) -> None:
    expected = f"REPLACE {deposition_id} {filename}"
    answer = input_fn(f"Type exactly '{expected}' to replace the draft file: ")
    if answer != expected:
        raise ToolError("File replacement confirmation did not match; no upload was attempted.")


def command_upload(args: argparse.Namespace) -> None:
    metadata, local_file = validate_local(args.metadata, args.pdf)
    _production_mutation_guard(args.environment, args.environment_explicit, args.allow_production)
    client = ZenodoClient(args.environment)
    draft, _ = _load_target(client, args.state, args.deposition_id)
    _ensure_unpublished(draft)
    differences = metadata_differences(metadata, draft.get("metadata") or {})
    if differences:
        raise ToolError("Remote metadata differs:\n- " + "\n- ".join(differences))
    existing = [
        item
        for item in (draft.get("files") or [])
        if isinstance(item, dict) and _remote_file_info(item)["name"] == local_file["name"]
    ]
    if existing:
        file_differences = verify_remote_file(draft, local_file)
        if not file_differences:
            print("The remote PDF already matches the local file; no upload was needed.")
            return
        if not args.replace:
            raise ToolError(
                "A different remote file has the same name. Pass --replace and confirm "
                "interactively to overwrite it in the unpublished draft."
            )
        _confirm_replace(_deposition_id(draft.get("id")), local_file["name"])
    bucket = _draft_links(draft).get("bucket")
    if not bucket:
        raise ToolError("Draft response did not include a bucket link.")
    client.upload(bucket, args.pdf)
    refreshed = client.get_draft(_deposition_id(draft.get("id")), _draft_links(draft).get("self"))
    verification = verify_remote_file(refreshed, local_file)
    if verification:
        raise ToolError("Upload completed but verification failed:\n- " + "\n- ".join(verification))
    save_state(args.state, _state_from_draft(args.environment, refreshed, "file_verified"))
    print("Upload verified. The draft remains unpublished.")
    print_draft_summary(refreshed, "Draft after upload")


def print_draft_summary(draft: dict[str, Any], heading: str = "Draft") -> None:
    metadata = draft.get("metadata") or {}
    links = draft.get("links") or {}
    files = [_remote_file_info(item) for item in draft.get("files") or [] if isinstance(item, dict)]
    summary = {
        "id": draft.get("id"),
        "state": draft.get("state"),
        "submitted": draft.get("submitted"),
        "title": metadata.get("title"),
        "creators": [item.get("name") for item in metadata.get("creators", []) if isinstance(item, dict)],
        "publication_date": metadata.get("publication_date"),
        "version": metadata.get("version"),
        "reserved_doi": _reserved_doi(draft),
        "files": files,
        "draft_url": links.get("html") or links.get("latest_draft_html"),
    }
    print(f"{heading}:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def command_inspect(args: argparse.Namespace) -> None:
    metadata = load_json(args.metadata)
    client = ZenodoClient(args.environment)
    draft, _ = _load_target(client, args.state, args.deposition_id)
    print_draft_summary(draft)
    differences = metadata_differences(metadata, draft.get("metadata") or {})
    if differences:
        print("Metadata differences:")
        for difference in differences:
            print(f"- {difference}")
    else:
        print("Local and remote metadata match.")


def _ci_detected() -> bool:
    return any(
        os.environ.get(name)
        for name in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "TF_BUILD", "BUILDKITE")
    )


def _validate_publish_link(url: str, deposition_id: int) -> None:
    parsed = urllib.parse.urlsplit(url)
    expected_path = f"/api/deposit/depositions/{deposition_id}/actions/publish"
    if (
        parsed.scheme != "https"
        or parsed.hostname != "zenodo.org"
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path.rstrip("/") != expected_path
        or parsed.query
        or parsed.fragment
    ):
        raise ToolError("Publish link is inconsistent with the production deposition.")


def command_publish(args: argparse.Namespace) -> None:
    if not args.publish:
        raise ToolError("Publication requires the explicit --publish flag.")
    if args.environment != "production" or not args.environment_explicit:
        raise ToolError("Publication requires explicit --environment production.")
    if args.deposition_id is None:
        raise ToolError("Publication requires an explicit --deposition-id.")
    if _ci_detected():
        raise ToolError("Publication is disabled in CI environments.")
    metadata, local_file = validate_local(args.metadata, args.pdf)
    client = ZenodoClient("production")
    deposition_id = _deposition_id(args.deposition_id)
    draft = client.get_draft(deposition_id)
    _ensure_unpublished(draft)
    differences = metadata_differences(metadata, draft.get("metadata") or {})
    differences.extend(verify_remote_file(draft, local_file))
    if not _reserved_doi(draft):
        differences.append("no reserved DOI is present")
    if differences:
        raise ToolError("Draft is not publishable:\n- " + "\n- ".join(differences))
    links = _draft_links(draft)
    publish_url = links.get("publish")
    if not publish_url:
        raise ToolError("Draft response did not include a publish link.")
    _validate_publish_link(publish_url, deposition_id)
    print_draft_summary(draft, "FINAL PUBLICATION SUMMARY")
    expected = f"PUBLISH {deposition_id}"
    answer = input(f"Type exactly '{expected}' to register the DOI and publish: ")
    if answer != expected:
        raise ToolError("Publication confirmation did not match; nothing was published.")
    result = client.publish(publish_url)
    print_draft_summary(result, "Published record")


def _add_common_files(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)


def _add_remote(parser: argparse.ArgumentParser, mutation: bool = False) -> None:
    parser.add_argument("--environment", choices=tuple(BASE_URLS))
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--deposition-id", type=int)
    if mutation:
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Second gate for create/upload mutations in production.",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate and manage a Zenodo whitepaper draft."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate metadata and PDF locally.")
    _add_common_files(validate)
    validate.set_defaults(handler=lambda args: validate_local(args.metadata, args.pdf))

    create = subparsers.add_parser("create-draft", help="Create or resume an unpublished draft.")
    _add_common_files(create)
    _add_remote(create, mutation=True)
    create.set_defaults(handler=command_create_draft)

    upload = subparsers.add_parser("upload", help="Upload and verify the PDF without publishing.")
    _add_common_files(upload)
    _add_remote(upload, mutation=True)
    upload.add_argument("--replace", action="store_true")
    upload.set_defaults(handler=command_upload)

    inspect = subparsers.add_parser("inspect", help="Read and compare a remote draft.")
    inspect.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    _add_remote(inspect)
    inspect.set_defaults(handler=command_inspect)

    publish = subparsers.add_parser(
        "publish", help="Manually publish after all production-only gates pass."
    )
    _add_common_files(publish)
    publish.add_argument("--environment", choices=tuple(BASE_URLS), required=True)
    publish.add_argument("--deposition-id", type=int, required=True)
    publish.add_argument("--publish", action="store_true")
    publish.set_defaults(handler=command_publish)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.environment_explicit = getattr(args, "environment", None) is not None
    if hasattr(args, "environment") and args.environment is None:
        args.environment = os.environ.get("ZENODO_ENV", "sandbox")
    try:
        args.handler(args)
        return 0
    except ToolError as exc:
        token = os.environ.get("ZENODO_ACCESS_TOKEN", "")
        print(f"ERROR: {sanitize(exc, (token,))}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

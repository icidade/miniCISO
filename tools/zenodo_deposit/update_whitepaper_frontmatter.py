#!/usr/bin/env python3
"""Update the versioned whitepaper DOCX front matter without external packages."""

from __future__ import annotations

import argparse
import html
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
LICENSE_TEXT = (
    "Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)"
)
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
ET.register_namespace("w", W_NS)


class FrontmatterError(RuntimeError):
    """The expected whitepaper structure was not found."""


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(W + "t"))


def _replace_text_nodes(paragraph_xml: str, text: str) -> str:
    matches = list(re.finditer(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", paragraph_xml, re.DOTALL))
    if not matches:
        raise FrontmatterError("Formatting paragraph has no text run.")
    escaped = html.escape(text, quote=False)
    parts: list[str] = []
    cursor = 0
    for index, match in enumerate(matches):
        parts.append(paragraph_xml[cursor : match.start()])
        replacement = escaped if index == 0 else ""
        parts.append(match.group(1) + replacement + match.group(3))
        cursor = match.end()
    parts.append(paragraph_xml[cursor:])
    return "".join(parts)


def update_document_xml(xml_bytes: bytes, doi: str | None = None) -> bytes:
    if doi and not DOI_PATTERN.fullmatch(doi):
        raise FrontmatterError("DOI must have the form 10.<registrant>/<suffix>.")
    try:
        xml = xml_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FrontmatterError("word/document.xml is not UTF-8.") from exc
    paragraphs = list(re.finditer(r"<w:p\b.*?</w:p>", xml, re.DOTALL))
    page_break_index = next(
        (
            index
            for index, match in enumerate(paragraphs)
            if re.search(r"<w:br\b[^>]*\bw:type=[\"']page[\"']", match.group(0))
        ),
        None,
    )
    if page_break_index is None:
        raise FrontmatterError("First-page break was not found.")
    license_index = next(
        (
            index
            for index, match in enumerate(paragraphs)
            if "Licensed under Creative Commons" in match.group(0)
        ),
        None,
    )
    text = LICENSE_TEXT + (f"  |  DOI: {doi}" if doi else "")
    if license_index is None:
        if page_break_index == 0:
            raise FrontmatterError("Cannot derive front-matter formatting.")
        page_break = paragraphs[page_break_index]
        previous = paragraphs[page_break_index - 1].group(0)
        license_xml = _replace_text_nodes(previous, text)
        xml = xml[: page_break.start()] + license_xml + xml[page_break.start() :]
    else:
        match = paragraphs[license_index]
        license_xml = _replace_text_nodes(match.group(0), text)
        xml = xml[: match.start()] + license_xml + xml[match.end() :]
    updated = xml.encode("utf-8")
    try:
        ET.fromstring(updated)
    except ET.ParseError as exc:
        raise FrontmatterError("Updated document XML is invalid.") from exc
    return updated


def update_docx(source: Path, output: Path, doi: str | None = None) -> None:
    if not source.is_file():
        raise FrontmatterError(f"Source DOCX not found: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as archive:
        if "word/document.xml" not in archive.namelist():
            raise FrontmatterError("Source is not a valid DOCX document.")
        updated_xml = update_document_xml(archive.read("word/document.xml"), doi)
        entries = [
            (
                info,
                updated_xml if info.filename == "word/document.xml" else archive.read(info),
            )
            for info in archive.infolist()
        ]
    with tempfile.NamedTemporaryFile(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as updated:
            for info, data in entries:
                updated.writestr(info, data)
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)


def verify_docx(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    matches = [
        paragraph_text(paragraph)
        for paragraph in root.iter(W + "p")
        if paragraph_text(paragraph).startswith("Licensed under Creative Commons")
    ]
    if len(matches) != 1:
        raise FrontmatterError(f"Expected one license line, found {len(matches)}.")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--doi", help="Reserved production DOI to place in the front matter.")
    args = parser.parse_args()
    update_docx(args.source, args.output, args.doi)
    print(verify_docx(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

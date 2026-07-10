#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)


def register_fonts() -> None:
    candidates = [
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("DejaVuSansMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for name, path in candidates:
        p = Path(path)
        if p.exists():
            pdfmetrics.registerFont(TTFont(name, str(p)))


def build_styles():
    base = getSampleStyleSheet()
    base["Normal"].fontName = "DejaVuSans"
    base["Normal"].fontSize = 10.5
    base["Normal"].leading = 14
    base["Normal"].alignment = TA_LEFT

    styles = {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="DejaVuSans-Bold",
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Heading2"],
            fontName="DejaVuSans",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#334155"),
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="DejaVuSans-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="DejaVuSans-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="DejaVuSans",
            fontSize=10.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontName="DejaVuSans",
            fontSize=10.5,
            leading=14,
            leftIndent=10,
            firstLineIndent=-8,
            spaceAfter=2,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["Normal"],
            fontName="DejaVuSans",
            fontSize=10.5,
            leading=14,
            leftIndent=12,
            borderPadding=6,
            borderColor=colors.HexColor("#CBD5E1"),
            borderWidth=0.8,
            borderLeft=True,
            textColor=colors.HexColor("#334155"),
            spaceBefore=4,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "meta",
            parent=base["Normal"],
            fontName="DejaVuSans",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontName="DejaVuSansMono",
            fontSize=8.8,
            leading=11,
            backColor=colors.HexColor("#F8FAFC"),
            borderColor=colors.HexColor("#CBD5E1"),
            borderWidth=0.6,
            borderPadding=6,
            leftIndent=2,
            rightIndent=2,
            spaceBefore=4,
            spaceAfter=6,
        ),
    }
    return styles


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def inline_md(text: str) -> str:
    text = esc(text)
    while "**" in text:
        a = text.find("**")
        b = text.find("**", a + 2)
        if b == -1:
            break
        inner = text[a + 2 : b]
        text = text[:a] + f"<b>{inner}</b>" + text[b + 2 :]
    while "`" in text:
        a = text.find("`")
        b = text.find("`", a + 1)
        if b == -1:
            break
        inner = text[a + 1 : b]
        text = text[:a] + f"<font name='DejaVuSansMono'>{esc(inner)}</font>" + text[b + 1 :]
    return text


def parse_markdown(md: str, styles) -> List:
    lines = md.splitlines()
    story: List = []
    in_code = False
    code_lines: List[str] = []
    paragraph_lines: List[str] = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(s.strip() for s in paragraph_lines).strip()
            if text:
                story.append(Paragraph(inline_md(text), styles["body"]))
            paragraph_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            story.append(Preformatted("\n".join(code_lines), styles["code"]))
            code_lines = []

    title_done = False
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            story.append(Spacer(1, 3))
            continue

        if stripped == "---":
            flush_paragraph()
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            text = stripped[2:].strip()
            if not title_done:
                story.append(Spacer(1, 28 * mm))
                story.append(Paragraph(inline_md(text), styles["title"]))
                title_done = True
            else:
                story.append(PageBreak())
                story.append(Paragraph(inline_md(text), styles["h1"]))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped[3:].strip()), styles["h1"]))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped[4:].strip()), styles["h2"]))
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped[2:].strip()), styles["quote"]))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph("• " + inline_md(stripped[2:].strip()), styles["bullet"]))
            continue

        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == ".":
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped), styles["bullet"]))
            continue

        if title_done and stripped.startswith("**") and stripped.endswith("**"):
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped), styles["h2"]))
            continue

        if title_done and stripped.startswith("**Status:**"):
            flush_paragraph()
            story.append(Paragraph(inline_md(stripped), styles["meta"]))
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    flush_code()
    return story


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVuSans", 9)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(195 * mm, 10 * mm, f"MiniCISO Staff Service Catalog v5 — {canvas.getPageNumber()}")
    canvas.restoreState()


def build_pdf(src: Path, out: Path) -> None:
    register_fonts()
    styles = build_styles()
    text = src.read_text(encoding="utf-8")
    story = parse_markdown(text, styles)
    doc = BaseDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="MiniCISO Staff Service Catalog v5",
        author="Hermes Agent / Irlan Cidade",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    template = PageTemplate(id="main", frames=[frame], onPage=add_page_number)
    doc.addPageTemplates([template])
    doc.build(story)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("output")
    args = ap.parse_args()
    build_pdf(Path(args.source), Path(args.output))


if __name__ == "__main__":
    main()

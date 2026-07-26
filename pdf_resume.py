"""Generate a real resume PDF while preserving the source profile photo."""

from __future__ import annotations

import html
import io
import re
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PhotoNotFoundError(ValueError):
    """Raised when no usable profile photo can be extracted."""


FONT_NAME = "NotoSansSC"
FONT_PATH = Path(__file__).resolve().parent / "assets" / "fonts" / "NotoSansSC.ttf"


def _register_font() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError("PDF 中文字体文件缺失")
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))


def extract_profile_photo(pdf_bytes: bytes) -> bytes:
    """Return the largest plausible embedded portrait image as PNG bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    candidates: list[tuple[int, bytes]] = []
    for page in reader.pages:
        for embedded in page.images:
            try:
                image = PILImage.open(io.BytesIO(embedded.data))
                image.load()
                width, height = image.size
                ratio = width / max(height, 1)
                if width >= 70 and height >= 70 and 0.45 <= ratio <= 1.45:
                    out = io.BytesIO()
                    image.convert("RGB").save(out, format="PNG")
                    candidates.append((width * height, out.getvalue()))
            except Exception:
                continue
    if not candidates:
        raise PhotoNotFoundError("未检测到可提取的简历照片")
    return max(candidates, key=lambda item: item[0])[1]


def _safe_markup(text: str) -> str:
    escaped = html.escape(text.strip())
    url_pattern = re.compile(r"(https?://[^\s<]+)")
    return url_pattern.sub(r'<link href="\1" color="#2563eb">\1</link>', escaped)


def _clean_line(line: str) -> tuple[str, str]:
    stripped = line.strip()
    level = "body"
    if stripped.startswith("### "):
        level, stripped = "heading", stripped[4:]
    elif stripped.startswith("## "):
        level, stripped = "heading", stripped[3:]
    elif stripped.startswith("# "):
        level, stripped = "title", stripped[2:]
    elif stripped.startswith(("- ", "* ", "• ", "□ ", "☑ ", "▪ ", "\uf0b7 ")):
        level, stripped = "bullet", stripped[2:]
    stripped = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped)
    stripped = re.sub(r"__([^_]+)__", r"\1", stripped)
    stripped = re.sub(r"`([^`]+)`", r"\1", stripped)
    return level, stripped


def _looks_like_section(text: str) -> bool:
    value = text.strip().rstrip("：:")
    sections = {
        "个人优势", "教育经历", "工作经历", "实习经历", "项目经历", "专业技能",
        "技能", "校园经历", "获奖经历", "证书", "自我评价", "求职意向",
    }
    return value in sections or (2 <= len(value) <= 12 and value.endswith("经历"))


def build_resume_pdf(rewritten_resume: str, photo_bytes: bytes, target_role: str) -> bytes:
    """Build an A4 resume PDF with a fixed photo in the first-page header."""
    if not rewritten_resume.strip():
        raise ValueError("优化简历内容为空")
    if not photo_bytes:
        raise PhotoNotFoundError("照片为空")

    _register_font()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title=f"{target_role}_针对性简历",
        author="AI 求职助手",
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "ResumeBody", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=8.8, leading=12.2, textColor=colors.HexColor("#263244"),
        spaceAfter=2.2,
    )
    bullet = ParagraphStyle(
        "ResumeBullet", parent=body, leftIndent=10, firstLineIndent=-7,
        bulletIndent=2, spaceAfter=1.8,
    )
    heading = ParagraphStyle(
        "ResumeHeading", parent=body, fontSize=11.5, leading=14,
        textColor=colors.HexColor("#17375e"), spaceBefore=5.5, spaceAfter=3,
    )
    title_style = ParagraphStyle(
        "ResumeTitle", parent=heading, fontSize=17, leading=20,
        textColor=colors.HexColor("#111827"), spaceBefore=0, spaceAfter=2,
    )
    role_style = ParagraphStyle(
        "ResumeRole", parent=body, fontSize=10.5, leading=14,
        textColor=colors.HexColor("#2563eb"), spaceAfter=4,
    )
    footer_style = ParagraphStyle(
        "ResumeFooter", parent=body, fontSize=7.2, textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
    )

    raw_lines = [line for line in rewritten_resume.replace("\r\n", "\n").split("\n")]
    nonempty = [(i, *_clean_line(line)) for i, line in enumerate(raw_lines) if line.strip()]
    header_items = nonempty[:4]
    consumed = {item[0] for item in header_items}
    header_flow = []
    if header_items:
        first = header_items[0][2]
        header_flow.append(Paragraph(_safe_markup(first), title_style))
    header_flow.append(Paragraph(_safe_markup(target_role), role_style))
    for _, _, value in header_items[1:]:
        if value.strip() != target_role.strip() and not _looks_like_section(value):
            header_flow.append(Paragraph(_safe_markup(value), body))

    photo = Image(io.BytesIO(photo_bytes), width=26 * mm, height=34 * mm, kind="proportional")
    header_table = Table([[header_flow, photo]], colWidths=[doc.width - 32 * mm, 32 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#93a4b8")),
    ]))
    story = [header_table, Spacer(1, 3 * mm)]

    for index, line in enumerate(raw_lines):
        if index in consumed or not line.strip():
            continue
        level, value = _clean_line(line)
        if not value:
            continue
        if level == "title" or level == "heading" or _looks_like_section(value):
            story.append(KeepTogether([
                Paragraph(_safe_markup(value.rstrip("：:")), heading),
            ]))
        elif level == "bullet" or re.match(r"^\d+[.、]\s*", value):
            story.append(Paragraph("• " + _safe_markup(value), bullet))
        else:
            story.append(Paragraph(_safe_markup(value), body))

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont(FONT_NAME, 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawCentredString(A4[0] / 2, 7 * mm, f"第 {document.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return buffer.getvalue()

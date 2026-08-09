"""Generate a real resume PDF with a modern two-column layout."""

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

SIDEBAR_WIDTH = 52 * mm
ACCENT = colors.HexColor("#1d4ed8")
LIGHT_BG = colors.HexColor("#eef3f8")
SIDEBAR_BG = colors.HexColor("#f1f5f9")
DIVIDER = colors.HexColor("#cbd5e1")
INK = colors.HexColor("#0f172a")
BODY_INK = colors.HexColor("#1f2937")
CONTACT_INK = colors.HexColor("#374151")

LEFT_SECTIONS = {
    "联系方式", "个人信息", "求职意向", "专业技能", "技能特长",
    "获奖证书", "证书", "语言", "语言能力", "兴趣爱好",
}


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
        "个人优势", "个人信息", "联系方式", "求职意向",
        "教育经历", "工作经历", "实习经历", "项目经历", "校园经历",
        "专业技能", "技能特长", "技能", "获奖经历", "获奖证书", "证书",
        "语言", "语言能力", "兴趣爱好", "自我评价",
    }
    return value in sections or (2 <= len(value) <= 12 and value.endswith("经历"))


def _parse_resume_sections(rewritten_resume: str) -> tuple[list[tuple[str, str]], list[tuple[str, list[tuple[str, str]]]]]:
    """Split markdown resume into (header_lines, sections)."""
    header: list[tuple[str, str]] = []
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    current: tuple[str, list[tuple[str, str]]] | None = None
    for line in rewritten_resume.replace("\r\n", "\n").split("\n"):
        if not line.strip():
            continue
        level, value = _clean_line(line)
        if not value:
            continue
        if level in ("title", "heading") or _looks_like_section(value):
            current = (value.rstrip("：:"), [])
            sections.append(current)
        elif current is None:
            if len(header) < 4:
                header.append((level, value))
            else:
                current = ("个人简历", [])
                sections.append(current)
                current[1].append((level, value))
        else:
            current[1].append((level, value))
    return header, sections


def build_resume_pdf(rewritten_resume: str, photo_bytes: bytes, target_role: str) -> bytes:
    """Build an A4 two-column resume PDF with a header block and sidebar."""
    if not rewritten_resume.strip():
        raise ValueError("优化简历内容为空")
    if not photo_bytes:
        raise PhotoNotFoundError("照片为空")

    _register_font()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=11 * mm,
        bottomMargin=12 * mm,
        title=f"{target_role}_针对性简历",
        author="AI 求职助手",
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "ResumeBody", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=9.5, leading=13.8, textColor=BODY_INK, spaceAfter=2.6,
    )
    bullet = ParagraphStyle(
        "ResumeBullet", parent=body, leftIndent=12, firstLineIndent=-8,
        bulletIndent=2, spaceAfter=2.4,
    )
    subhead = ParagraphStyle(
        "ResumeSubhead", parent=body, fontSize=10.2, leading=13.5,
        textColor=INK, spaceBefore=2, spaceAfter=1.5,
    )
    right_heading = ParagraphStyle(
        "RightHeading", parent=body, fontSize=12, leading=15,
        textColor=INK, spaceBefore=0, spaceAfter=0,
    )
    name_style = ParagraphStyle(
        "ResumeName", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=20, leading=23, textColor=INK, spaceAfter=2,
    )
    role_style = ParagraphStyle(
        "ResumeRole", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=11.5, leading=15, textColor=ACCENT, spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "ResumeContact", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=9.3, leading=13, textColor=CONTACT_INK, spaceAfter=1.2,
    )
    sidebar_heading = ParagraphStyle(
        "SidebarHeading", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=10.5, leading=13.5, textColor=INK, spaceAfter=0,
    )
    sidebar_body = ParagraphStyle(
        "SidebarBody", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=8.8, leading=12.6, textColor=BODY_INK, spaceAfter=2.4,
    )
    sidebar_bullet = ParagraphStyle(
        "SidebarBullet", parent=sidebar_body, leftIndent=9, firstLineIndent=-6,
        bulletIndent=1, spaceAfter=2,
    )
    footer_style = ParagraphStyle(
        "ResumeFooter", parent=body, fontSize=7.2,
        textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER,
    )

    header, sections = _parse_resume_sections(rewritten_resume)

    # ---- 顶部信息区 ----
    name = header[0][1] if header else "简历"
    header_left = [
        Paragraph(_safe_markup(name), name_style),
        Paragraph(_safe_markup(target_role), role_style),
    ]
    contacts = [
        value
        for _level, value in header[1:]
        if value.strip() != target_role.strip() and not _looks_like_section(value)
    ]
    for contact in contacts[:4]:
        header_left.append(Paragraph(_safe_markup(contact), contact_style))

    photo_table = Table(
        [[Image(io.BytesIO(photo_bytes), width=24 * mm, height=30 * mm, kind="proportional")]],
        colWidths=[24 * mm],
        rowHeights=[30 * mm],
    )
    photo_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, DIVIDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    header_table = Table([[header_left, photo_table]], colWidths=[doc.width - 28 * mm, 28 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 6 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 1.2, INK),
    ]))

    # ---- 左侧信息栏 / 右侧主内容 ----
    left_pad_lr = 5 * mm
    right_pad_l = 6 * mm
    right_pad_r = 4 * mm
    usable_left = SIDEBAR_WIDTH - 2 * left_pad_lr
    usable_right = (doc.width - SIDEBAR_WIDTH) - right_pad_l - right_pad_r

    def section_header(text: str, width: float, sidebar: bool = False) -> Table:
        bar = Paragraph("", ParagraphStyle("accentbar", fontName=FONT_NAME, fontSize=1))
        head_style = sidebar_heading if sidebar else right_heading
        table = Table(
            [[bar, Paragraph(_safe_markup(text), head_style)]],
            colWidths=[3 * mm, width - 3 * mm],
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.7, DIVIDER),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 0), (0, 0), 0),
            ("BOTTOMPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return table

    def render_items(
        items: list[tuple[str, str]],
        body_style: ParagraphStyle,
        bullet_style: ParagraphStyle,
        subhead_style: ParagraphStyle,
    ) -> list:
        flow = []
        for level, value in items:
            if level == "bullet" or re.match(r"^\d+[.、]\s*", value):
                flow.append(Paragraph("• " + _safe_markup(value), bullet_style))
            elif level == "heading":
                flow.append(Paragraph(_safe_markup(value), subhead_style))
            else:
                flow.append(Paragraph(_safe_markup(value), body_style))
        return flow

    sidebar_flow: list = []
    main_flow: list = []
    for section_name, items in sections:
        if section_name in LEFT_SECTIONS:
            sidebar_flow.append(section_header(section_name, usable_left, sidebar=True))
            sidebar_flow.extend(render_items(items, sidebar_body, sidebar_bullet, sidebar_heading))
        else:
            main_flow.append(section_header(section_name, usable_right))
            main_flow.extend(render_items(items, body, bullet, subhead))

    has_contact_section = any(name in ("联系方式", "个人信息") for name, _ in sections)
    if not has_contact_section and contacts:
        auto_contacts = [section_header("联系方式", usable_left, sidebar=True)]
        auto_contacts.extend(Paragraph(_safe_markup(c), sidebar_body) for c in contacts[:4])
        sidebar_flow = auto_contacts + sidebar_flow

    if not main_flow:
        default_items = [(level, value) for level, value in header[4:]]
        if default_items:
            main_flow.append(section_header("个人简历", usable_right))
            main_flow.extend(render_items(default_items, body, bullet, subhead))

    two_col = Table(
        [[sidebar_flow, main_flow]],
        colWidths=[SIDEBAR_WIDTH, doc.width - SIDEBAR_WIDTH],
    )
    two_col.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), SIDEBAR_BG),
        ("BACKGROUND", (1, 0), (1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), left_pad_lr),
        ("RIGHTPADDING", (0, 0), (0, 0), left_pad_lr),
        ("TOPPADDING", (0, 0), (0, 0), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6 * mm),
        ("LEFTPADDING", (1, 0), (1, 0), right_pad_l),
        ("RIGHTPADDING", (1, 0), (1, 0), right_pad_r),
        ("TOPPADDING", (1, 0), (1, 0), 5 * mm),
        ("BOTTOMPADDING", (1, 0), (1, 0), 6 * mm),
    ]))

    story = [header_table, Spacer(1, 3 * mm), two_col]

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont(FONT_NAME, 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawCentredString(A4[0] / 2, 7 * mm, f"第 {document.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return buffer.getvalue()

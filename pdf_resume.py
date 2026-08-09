"""Generate a real resume PDF: modern two-column layout with a stable single-column fallback."""

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
    HRFlowable,
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
LINK_COLOR = colors.HexColor("#1d4ed8")
LIGHT_BG = colors.HexColor("#eef3f8")
SIDEBAR_BG = colors.HexColor("#f1f5f9")
DIVIDER = colors.HexColor("#cbd5e1")
INK = colors.HexColor("#0f172a")
BODY_INK = colors.HexColor("#111827")
LEFT_INK = colors.HexColor("#1f2937")
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


def _shorten_url(url: str) -> str:
    """Shorten a URL for display while keeping it recognizable (no fabrication)."""
    cleaned = url.strip().rstrip(".,;:!?。，；：！？)")
    match = re.match(r"^(?:https?://)?(?:www\.)?([^/]+)(/.*)?$", cleaned, re.IGNORECASE)
    if not match:
        return cleaned
    domain = match.group(1)
    path = (match.group(2) or "").rstrip("/")
    segments = [seg for seg in path.split("/") if seg]
    kept = segments[:2]
    shown = domain + ("/" + "/".join(kept) if kept else "")
    if len(segments) > 2:
        shown += "/…"
    if len(shown) > 34:
        shown = shown[:34] + "…"
    return shown


def _safe_markup(text: str, shorten_links: bool = True) -> str:
    escaped = html.escape(text.strip())
    url_pattern = re.compile(r"https?://[^\s<]+")

    def _replace(match):
        raw = match.group(0)
        url = raw.rstrip(".,;:!?。，；：！？)")
        if not url:
            return raw
        label = _shorten_url(url) if shorten_links else url
        return f'<link href="{url}" color="#1d4ed8">{label}</link>'

    return url_pattern.sub(_replace, escaped)


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


def _parse_resume_sections(
    rewritten_resume: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, list[tuple[str, str]]]]]:
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


def _content_is_long(rewritten_resume: str) -> bool:
    """Heuristic: very long content goes straight to the stable single-column layout."""
    lines = rewritten_resume.splitlines()
    bullets = sum(1 for line in lines if line.strip().startswith(("- ", "* ", "• ")))
    return len(rewritten_resume) > 1400 or bullets > 25 or len(lines) > 90


def _make_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "ResumeBody", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=9.5, leading=13.8, textColor=BODY_INK, spaceAfter=2.6,
        ),
        "bullet": ParagraphStyle(
            "ResumeBullet", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=9.5, leading=13.8, textColor=BODY_INK,
            leftIndent=12, firstLineIndent=-8, bulletIndent=2, spaceAfter=2.4,
        ),
        "subhead": ParagraphStyle(
            "ResumeSubhead", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=10.2, leading=13.5, textColor=INK, spaceBefore=2, spaceAfter=1.5,
        ),
        "right_heading": ParagraphStyle(
            "RightHeading", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=12, leading=15, textColor=INK, spaceBefore=3, spaceAfter=1,
        ),
        "name": ParagraphStyle(
            "ResumeName", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=20, leading=23, textColor=INK, spaceAfter=2,
        ),
        "role": ParagraphStyle(
            "ResumeRole", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=11.5, leading=15, textColor=ACCENT, spaceAfter=4,
        ),
        "contact": ParagraphStyle(
            "ResumeContact", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=9.3, leading=13, textColor=CONTACT_INK, spaceAfter=1.2,
        ),
        "sidebar_heading": ParagraphStyle(
            "SidebarHeading", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=10.5, leading=13.5, textColor=INK, spaceBefore=4, spaceAfter=1,
        ),
        "sidebar_body": ParagraphStyle(
            "SidebarBody", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=8.8, leading=12.6, textColor=LEFT_INK, spaceAfter=2.4,
        ),
        "sidebar_bullet": ParagraphStyle(
            "SidebarBullet", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=8.8, leading=12.6, textColor=LEFT_INK,
            leftIndent=9, firstLineIndent=-6, bulletIndent=1, spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "ResumeFooter", parent=styles["BodyText"], fontName=FONT_NAME,
            fontSize=7.2, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER,
        ),
    }


def _build_header_table(
    header: list[tuple[str, str]],
    target_role: str,
    photo_bytes: bytes,
    total_width: float,
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Top info block: name + role + contacts on the left, photo on the right."""
    name = header[0][1] if header else "简历"
    left = [
        Paragraph(_safe_markup(name), styles["name"]),
        Paragraph(_safe_markup(target_role), styles["role"]),
    ]
    contacts = [
        value
        for _level, value in header[1:]
        if value.strip() != target_role.strip() and not _looks_like_section(value)
    ]
    for contact in contacts[:4]:
        left.append(Paragraph(_safe_markup(contact), styles["contact"]))

    photo_table = Table(
        [[Image(io.BytesIO(photo_bytes), width=24 * mm, height=30 * mm, kind="proportional")]],
        colWidths=[24 * mm],
        rowHeights=[30 * mm],
    )
    photo_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, DIVIDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    header_table = Table([[left, photo_table]], colWidths=[total_width - 28 * mm, 28 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 6 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748b")),
    ]))
    return header_table


def _section_heading(text: str, style: ParagraphStyle, sidebar: bool = False) -> list:
    """Resume-style heading: short accent bar + dark title + light divider."""
    if sidebar:
        return [
            Paragraph(_safe_markup(text), style),
            HRFlowable(width="100%", thickness=0.5, color=DIVIDER, spaceBefore=1, spaceAfter=4),
        ]
    return [
        HRFlowable(width=14 * mm, thickness=2, color=ACCENT, spaceBefore=4, spaceAfter=1.5),
        Paragraph(_safe_markup(text), style),
        HRFlowable(width="100%", thickness=0.5, color=DIVIDER, spaceBefore=1, spaceAfter=4),
    ]


def _render_items(
    items: list[tuple[str, str]],
    styles: dict[str, ParagraphStyle],
    sidebar: bool = False,
) -> list:
    body_style = styles["sidebar_body"] if sidebar else styles["body"]
    bullet_style = styles["sidebar_bullet"] if sidebar else styles["bullet"]
    subhead_style = styles["sidebar_heading"] if sidebar else styles["subhead"]
    flow = []
    for level, value in items:
        if level == "bullet" or re.match(r"^\d+[.、]\s*", value):
            flow.append(Paragraph("• " + _safe_markup(value), bullet_style))
        elif level == "heading":
            flow.append(Paragraph(_safe_markup(value), subhead_style))
        else:
            flow.append(Paragraph(_safe_markup(value), body_style))
    return flow


def _add_page_number(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont(FONT_NAME, 7)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawCentredString(A4[0] / 2, 7 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def _modern_page(canvas, document) -> None:
    """Draw the full-height sidebar background, then the page number."""
    canvas.saveState()
    canvas.setFillColor(SIDEBAR_BG)
    canvas.rect(12 * mm, 12 * mm, SIDEBAR_WIDTH, A4[1] - 11 * mm - 12 * mm, stroke=0, fill=1)
    canvas.restoreState()
    _add_page_number(canvas, document)


def _build_modern_pdf(
    rewritten_resume: str,
    photo_bytes: bytes,
    target_role: str,
    styles: dict[str, ParagraphStyle],
) -> bytes:
    """Two-column modern layout. Cells only contain Paragraph/HR/Spacer so rows can split."""
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
    header, sections = _parse_resume_sections(rewritten_resume)
    header_table = _build_header_table(header, target_role, photo_bytes, doc.width, styles)

    left_pad_lr = 5 * mm
    right_pad_l = 6 * mm
    right_pad_r = 4 * mm
    usable_left = SIDEBAR_WIDTH - 2 * left_pad_lr
    usable_right = (doc.width - SIDEBAR_WIDTH) - right_pad_l - right_pad_r

    sidebar_flow: list = []
    main_flow: list = []
    for section_name, items in sections:
        if section_name in LEFT_SECTIONS:
            sidebar_flow.extend(_section_heading(section_name, styles["sidebar_heading"], sidebar=True))
            sidebar_flow.extend(_render_items(items, styles, sidebar=True))
        else:
            main_flow.extend(_section_heading(section_name, styles["right_heading"]))
            main_flow.extend(_render_items(items, styles, sidebar=False))

    contacts = [
        value
        for _level, value in header[1:]
        if value.strip() != target_role.strip() and not _looks_like_section(value)
    ]
    has_contact_section = any(name in ("联系方式", "个人信息") for name, _ in sections)
    if not has_contact_section and contacts:
        auto = _section_heading("联系方式", styles["sidebar_heading"], sidebar=True)
        auto.extend(Paragraph(_safe_markup(c), styles["sidebar_body"]) for c in contacts[:4])
        sidebar_flow = auto + sidebar_flow

    if not main_flow:
        default_items = [(level, value) for level, value in header[4:]]
        if default_items:
            main_flow.extend(_section_heading("个人简历", styles["right_heading"]))
            main_flow.extend(_render_items(default_items, styles, sidebar=False))

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
    doc.build(story, onFirstPage=_modern_page, onLaterPages=_modern_page)
    return buffer.getvalue()


def _build_single_column_pdf(
    rewritten_resume: str,
    photo_bytes: bytes,
    target_role: str,
    styles: dict[str, ParagraphStyle],
) -> bytes:
    """Stable single-column layout: header + dark sections with accent underlines."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{target_role}_针对性简历",
        author="AI 求职助手",
    )
    header, sections = _parse_resume_sections(rewritten_resume)
    header_table = _build_header_table(header, target_role, photo_bytes, doc.width, styles)
    story = [header_table, Spacer(1, 4 * mm)]

    if sections:
        for section_name, items in sections:
            story.extend(_section_heading(section_name, styles["right_heading"]))
            story.extend(_render_items(items, styles, sidebar=False))
    else:
        story.extend(_section_heading("个人简历", styles["right_heading"]))
        story.extend(
            Paragraph(_safe_markup(value), styles["body"])
            for _level, value in header
        )

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return buffer.getvalue()


def build_resume_pdf(rewritten_resume: str, photo_bytes: bytes, target_role: str) -> bytes:
    """Build a resume PDF: modern two-column when safe, stable single-column otherwise."""
    if not rewritten_resume.strip():
        raise ValueError("优化简历内容为空")
    if not photo_bytes:
        raise PhotoNotFoundError("照片为空")

    _register_font()
    styles = _make_styles()

    if _content_is_long(rewritten_resume):
        return _build_single_column_pdf(rewritten_resume, photo_bytes, target_role, styles)

    try:
        return _build_modern_pdf(rewritten_resume, photo_bytes, target_role, styles)
    except Exception:
        # 现代双栏布局遇到无法排版的内容时，自动降级为稳定单栏模板。
        return _build_single_column_pdf(rewritten_resume, photo_bytes, target_role, styles)

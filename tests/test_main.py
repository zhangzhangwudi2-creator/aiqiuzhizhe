import io

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

import main
from pdf_resume import PhotoNotFoundError, build_resume_pdf, extract_profile_photo
from quota import SlidingWindowRateLimiter, TTLCache, build_cache_key
from schemas import AnalysisResult
from evaluation.rubric import evaluate_case


def test_validate_jd_rejects_empty_text():
    with pytest.raises(HTTPException) as exc:
        main._validate_jd("   ")
    assert exc.value.status_code == 400


def test_validate_jd_rejects_oversized_text():
    with pytest.raises(HTTPException) as exc:
        main._validate_jd("a" * (main.MAX_JD_CHARS + 1))
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_parse_resume_rejects_non_pdf():
    upload = UploadFile(filename="resume.txt", file=io.BytesIO(b"hello"))
    upload.headers = {"content-type": "text/plain"}
    with pytest.raises(HTTPException) as exc:
        await main._parse_resume(upload)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_parse_resume_rejects_pdf_without_text():
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    buffer.seek(0)
    upload = UploadFile(filename="resume.pdf", file=buffer, headers={"content-type": "application/pdf"})
    with pytest.raises(HTTPException) as exc:
        await main._parse_resume(upload)
    assert exc.value.status_code == 400


def test_extract_pdf_rejects_invalid_file():
    with pytest.raises(HTTPException) as exc:
        main._extract_pdf_text(b"not a pdf")
    assert exc.value.status_code == 400


def _pdf_with_photo() -> bytes:
    photo = io.BytesIO()
    PILImage.new("RGB", (180, 240), "#6b8afd").save(photo, format="PNG")
    photo.seek(0)
    output = io.BytesIO()
    page = canvas.Canvas(output, pagesize=A4)
    page.drawString(50, 780, "Resume")
    page.drawImage(ImageReader(photo), 450, 700, width=72, height=96, mask="auto")
    page.save()
    return output.getvalue()


def test_extract_profile_photo_finds_embedded_portrait():
    extracted = extract_profile_photo(_pdf_with_photo())
    image = PILImage.open(io.BytesIO(extracted))
    assert image.width >= 70
    assert image.height >= 70


def test_extract_profile_photo_rejects_pdf_without_photo():
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    with pytest.raises(PhotoNotFoundError):
        extract_profile_photo(output.getvalue())


def test_build_resume_pdf_keeps_photo_and_text():
    photo = extract_profile_photo(_pdf_with_photo())
    result = build_resume_pdf(
        "张凡\nAI产品经理实习生\n19306241281 | 杭州\nhttps://github.com/example\n项目经历\n- 完成需求分析与产品迭代",
        photo,
        "AI产品经理实习生",
    )
    reader = PdfReader(io.BytesIO(result))
    assert len(reader.pages) == 1
    assert len(reader.pages[0].images) >= 1
    assert "张凡" in (reader.pages[0].extract_text() or "")


def test_build_resume_pdf_with_sections_and_styles():
    photo = extract_profile_photo(_pdf_with_photo())
    content = (
        "陈志远\nAI产品运营实习生\nchenzhiyuan@example.com | 138-0000-0000 | 杭州\n"
        "https://github.com/chenzhiyuan\n"
        "教育经历\n华中科技大学 计算机科学与技术本科\n"
        "项目经历\n- 搭建 AI 求职助手：FastAPI 后端，调用 DeepSeek API\n- 完成需求分析与功能迭代\n"
        "专业技能\n- **Python**、FastAPI\n"
        "获奖证书\n暂无\n"
    )
    result = build_resume_pdf(content, photo, "AI产品运营实习生")
    assert result.startswith(b"%PDF")
    assert len(result) > 1000
    reader = PdfReader(io.BytesIO(result))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "陈志远" in text
    assert "AI产品运营实习生" in text
    assert "教育经历" in text
    assert "项目经历" in text
    assert "专业技能" in text
    assert "获奖证书" in text
    assert "华中科技大学" in text


def test_build_resume_pdf_modern_two_column_layout():
    photo = extract_profile_photo(_pdf_with_photo())
    content = (
        "陈志远\nAI产品运营实习生\nchenzhiyuan@example.com | 138-0000-0000 | 杭州\n"
        "https://github.com/chenzhiyuan\n"
        "专业技能\n- Python、FastAPI\n- Prompt 工程\n"
        "教育经历\n华中科技大学 计算机科学与技术本科\n"
        "项目经历\n- 搭建 AI 求职助手：FastAPI 后端，调用 DeepSeek API\n"
        "实习经历\n- 参与产品需求分析与功能迭代\n"
        "获奖证书\n暂无\n"
    )
    result = build_resume_pdf(content, photo, "AI产品运营实习生")
    assert result.startswith(b"%PDF")
    assert len(result) > 1500
    reader = PdfReader(io.BytesIO(result))
    assert len(reader.pages) <= 2
    assert sum(len(page.images) for page in reader.pages) >= 1
    text = "".join(page.extract_text() or "" for page in reader.pages)
    for token in (
        "陈志远", "AI产品运营实习生", "专业技能", "教育经历",
        "项目经历", "实习经历", "获奖证书", "华中科技大学", "FastAPI",
    ):
        assert token in text


def test_build_resume_pdf_fallback_without_sections():
    photo = extract_profile_photo(_pdf_with_photo())
    result = build_resume_pdf(
        "张三\n电话 138-0000-0000\n擅长 Python 与 FastAPI\n做过三个项目",
        photo,
        "AI产品运营实习生",
    )
    assert result.startswith(b"%PDF")
    reader = PdfReader(io.BytesIO(result))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "张三" in text
    assert "Python" in text


def test_build_resume_pdf_without_photo_raises():
    import pytest

    with pytest.raises(PhotoNotFoundError):
        build_resume_pdf("张凡\n项目经历", b"", "AI产品经理实习生")


def test_export_pdf_endpoint_returns_real_pdf_with_photo():
    client = TestClient(main.app)
    response = client.post(
        "/export-resume-pdf",
        files={"resume": ("resume.pdf", _pdf_with_photo(), "application/pdf")},
        data={"rewritten_resume": "张凡\n项目经历\n- 完成产品迭代", "target_role": "AI产品实习生"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_export_pdf_endpoint_refuses_to_drop_photo():
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    client = TestClient(main.app)
    response = client.post(
        "/export-resume-pdf",
        files={"resume": ("resume.pdf", output.getvalue(), "application/pdf")},
        data={"rewritten_resume": "张凡\n项目经历", "target_role": "AI产品实习生"},
    )
    assert response.status_code == 422
    assert "停止导出" in response.json()["detail"]


def test_analysis_schema_accepts_valid_output():
    result = AnalysisResult.model_validate({
        "overall_score": 80,
        "strengths": [{"point": "项目", "detail": "有真实部署"}],
        "skill_gaps": [{"skill": "测试", "importance": "高", "current_status": "较少", "improvement_suggestion": "补充测试"}],
        "resume_tips": [{"section": "项目", "issue": "缺少数据", "rewrite_suggestion": "补充评测结果"}],
        "interview_questions": [{"question": "如何评测？", "intent": "评测能力", "difficulty": "中等"}],
    })
    assert result.overall_score == 80


def test_analysis_schema_rejects_invalid_score():
    with pytest.raises(ValueError):
        AnalysisResult.model_validate({
            "overall_score": 120,
            "strengths": [],
            "skill_gaps": [],
            "resume_tips": [],
            "interview_questions": [],
        })


def test_cache_key_is_stable_and_operation_specific():
    assert build_cache_key("analyze", "resume", "jd") == build_cache_key("analyze", "resume", "jd")
    assert build_cache_key("analyze", "resume", "jd") != build_cache_key("rewrite", "resume", "jd")


def test_ttl_cache_returns_saved_value():
    cache = TTLCache(max_entries=2, ttl_seconds=60)
    cache.set("key", {"score": 80})
    assert cache.get("key") == {"score": 80}


def test_rate_limiter_blocks_after_limit():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.check("visitor")[0] is True
    assert limiter.check("visitor")[0] is True
    allowed, retry_after = limiter.check("visitor")
    assert allowed is False
    assert retry_after > 0


def test_client_identity_trusts_rightmost_forwarded_hop():
    identity = main._client_identity_from_parts(
        "1.2.3.4, 5.6.7.8",
        "203.0.113.1",
        trust_forwarded=True,
    )
    assert identity == "5.6.7.8"


def test_client_identity_ignores_forwarded_when_not_trusted():
    identity = main._client_identity_from_parts(
        "1.2.3.4, 5.6.7.8",
        "203.0.113.1",
        trust_forwarded=False,
    )
    assert identity == "203.0.113.1"


def test_client_identity_handles_empty_forwarded():
    assert (
        main._client_identity_from_parts("  ,  ", None, trust_forwarded=True)
        == "unknown"
    )
    assert (
        main._client_identity_from_parts("", "203.0.113.1", trust_forwarded=True)
        == "203.0.113.1"
    )
    assert (
        main._client_identity_from_parts("1.2.3.4", None, trust_forwarded=True)
        == "1.2.3.4"
    )


def test_quality_rubric_accepts_matching_output():
    case = {
        "case_id": "demo",
        "expectations": {
            "score_range": [70, 80],
            "required_terms": ["工作流", "评测"],
            "forbidden_terms": ["百万用户"],
        },
        "output": {
            "overall_score": 75,
            "strengths": [{"point": "工作流", "detail": "有项目实践"}],
            "skill_gaps": [{"skill": "评测", "importance": "高", "current_status": "较少", "improvement_suggestion": "建立测试集"}],
            "resume_tips": [{"section": "项目", "issue": "数据不足", "rewrite_suggestion": "补充验证结果"}],
            "interview_questions": [{"question": "如何验证？", "intent": "评测思维", "difficulty": "中等"}],
        },
    }
    assert evaluate_case(case).passed is True


def test_quality_rubric_rejects_unsupported_claim():
    case = {
        "case_id": "hallucination",
        "expectations": {
            "score_range": [0, 100],
            "required_terms": [],
            "forbidden_terms": ["百万用户"],
        },
        "output": {
            "overall_score": 80,
            "strengths": [{"point": "用户", "detail": "拥有百万用户"}],
            "skill_gaps": [{"skill": "测试", "importance": "中", "current_status": "较少", "improvement_suggestion": "补充"}],
            "resume_tips": [{"section": "项目", "issue": "数据不足", "rewrite_suggestion": "补充"}],
            "interview_questions": [{"question": "为什么？", "intent": "判断", "difficulty": "简单"}],
        },
    }
    assert evaluate_case(case).passed is False

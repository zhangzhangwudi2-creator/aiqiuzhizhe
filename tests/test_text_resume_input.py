"""Tests for paste-text resume input on analyze and rewrite endpoints."""

import json

from fastapi.testclient import TestClient

import main


VALID_ANALYSIS = {
    "overall_score": 78,
    "strengths": [{"point": "工作流", "detail": "有可运行项目"}],
    "skill_gaps": [
        {
            "skill": "评测",
            "importance": "高",
            "current_status": "样本较少",
            "improvement_suggestion": "扩充人工标注样本",
        }
    ],
    "resume_tips": [
        {
            "section": "项目经历",
            "issue": "缺少评测数字",
            "rewrite_suggestion": "补充测试集规模和通过率",
        }
    ],
    "interview_questions": [
        {
            "question": "如何判断 Prompt 改进有效？",
            "intent": "考察评测思维",
            "difficulty": "中等",
        }
    ],
}

RESUME_TEXT = (
    "张凡\n某大学计算机专业\n"
    "项目：搭建 AI 求职助手，使用 FastAPI 与 DeepSeek API 完成简历岗位匹配分析"
)


def setup_function() -> None:
    main.response_cache.clear()
    main.rate_limiter.clear()


def test_analyze_with_resume_text_only(monkeypatch):
    async def fake_chat_completion(**_kwargs):
        return json.dumps(VALID_ANALYSIS, ensure_ascii=False)

    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/analyze",
        data={"jd_text": "AI 应用实习生", "resume_text": RESUME_TEXT},
    )

    assert response.status_code == 200
    assert response.json()["overall_score"] == 78


def test_analyze_with_short_resume_text_returns_400():
    client = TestClient(main.app)
    response = client.post(
        "/analyze",
        data={"jd_text": "AI 应用实习生", "resume_text": "太短了"},
    )
    assert response.status_code == 400
    assert "过短" in response.json()["detail"]


def test_analyze_without_resume_returns_400():
    client = TestClient(main.app)
    response = client.post("/analyze", data={"jd_text": "AI 应用实习生"})
    assert response.status_code == 400
    assert "简历" in response.json()["detail"]


def test_rewrite_with_resume_text(monkeypatch):
    async def fake_chat_completion(**_kwargs):
        return "# 张凡\n## AI应用实习生\n### 项目经历\nAI求职助手"

    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/rewrite-resume",
        data={"jd_text": "AI 应用实习生", "resume_text": RESUME_TEXT},
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == "AI 应用实习生"
    assert "AI求职助手" in response.json()["rewritten_resume"]


def test_analyze_pdf_upload_still_works(monkeypatch):
    async def fake_parse_resume(_resume):
        return RESUME_TEXT

    async def fake_chat_completion(**_kwargs):
        return json.dumps(VALID_ANALYSIS, ensure_ascii=False)

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        data={"jd_text": "AI 应用实习生"},
    )

    assert response.status_code == 200

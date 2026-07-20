"""API-level tests with the model call replaced by a deterministic fake."""

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


def setup_function() -> None:
    main.response_cache.clear()
    main.rate_limiter.clear()


def test_analyze_endpoint_returns_validated_model_output(monkeypatch):
    async def fake_parse_resume(_resume):
        return "候选人有 AI 工作流项目经验"

    async def fake_chat_completion(**_kwargs):
        return json.dumps(VALID_ANALYSIS, ensure_ascii=False)

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        data={"jd_text": "AI 应用实习生，要求了解 Prompt 与评测"},
    )

    assert response.status_code == 200
    assert response.json()["overall_score"] == 78
    assert response.json()["skill_gaps"][0]["skill"] == "评测"


def test_analyze_endpoint_reuses_cached_result(monkeypatch):
    calls = 0

    async def fake_parse_resume(_resume):
        return "同一份匿名简历"

    async def fake_chat_completion(**_kwargs):
        nonlocal calls
        calls += 1
        return json.dumps(VALID_ANALYSIS, ensure_ascii=False)

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    request = {
        "files": {"resume": ("resume.pdf", b"fake", "application/pdf")},
        "data": {"jd_text": "AI 应用实习生"},
    }
    first = client.post("/analyze", **request)
    second = client.post("/analyze", **request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls == 1

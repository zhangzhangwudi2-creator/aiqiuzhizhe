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


def test_rewrite_endpoint_uses_explicit_target_role(monkeypatch):
    captured = {}

    async def fake_parse_resume(_resume):
        return "张凡\n原求职方向：内容运营\n项目：AI求职助手"

    async def fake_chat_completion(**kwargs):
        captured.update(kwargs)
        return "# 张凡\n## AI产品经理实习生\n### 项目经历\nAI求职助手"

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/rewrite-resume",
        files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        data={
            "jd_text": "负责AI产品需求分析、功能迭代和数据复盘",
            "target_role": "AI产品经理实习生",
        },
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == "AI产品经理实习生"
    assert "<TARGET_ROLE>" in captured["user_prompt"]
    assert "AI产品经理实习生" in captured["user_prompt"]
    assert "不得保留原求职岗位" in captured["system_prompt"]


def test_rewrite_endpoint_rejects_fabricated_facts(monkeypatch):
    async def fake_parse_resume(_resume):
        return "测试候选人\n某大学\n杭州"

    async def fake_chat_completion(**_kwargs):
        return "# 张伟\nXX大学\n北京"

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)

    client = TestClient(main.app)
    response = client.post(
        "/rewrite-resume",
        files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        data={"jd_text": "AI产品运营实习生", "target_role": "AI产品运营实习生"},
    )

    assert response.status_code == 502
    assert "事实一致性校验" in response.json()["detail"]


def test_analyze_returns_429_when_rate_limit_exceeded(monkeypatch):
    async def fake_parse_resume(_resume):
        return "同一份匿名简历"

    async def fake_chat_completion(**_kwargs):
        return json.dumps(VALID_ANALYSIS, ensure_ascii=False)

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)
    monkeypatch.setenv("TRUST_X_FORWARDED_FOR", "false")

    client = TestClient(main.app)
    response = None
    for index in range(main.RATE_LIMIT_REQUESTS + 1):
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", b"fake", "application/pdf")},
            data={"jd_text": f"AI 应用实习生 {index}"},
            headers={"X-Forwarded-For": f"1.2.3.{index}"},
        )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rewrite_endpoint_infers_target_role(monkeypatch):
    captured = {}

    async def fake_parse_resume(_resume):
        return "匿名简历"

    async def fake_chat_completion(**kwargs):
        captured.update(kwargs)
        return "# 匿名用户\n## AI产品经理实习生"

    monkeypatch.setattr(main, "_parse_resume", fake_parse_resume)
    monkeypatch.setattr(main, "_chat_completion", fake_chat_completion)
    client = TestClient(main.app)
    response = client.post(
        "/rewrite-resume",
        files={"resume": ("resume.pdf", b"fake", "application/pdf")},
        data={"jd_text": "AI产品经理（实习生） 150-200元/天\n负责需求分析和功能迭代"},
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == "AI产品经理（实习生）"
    assert "AI产品经理（实习生）" in captured["user_prompt"]


def test_infer_target_role_uses_jd_keywords():
    assert main._infer_target_role("负责海外 AI 短剧后期剪辑、音效和字幕适配") == "AI短剧后期剪辑实习生"

"""Tests for target_role auto-inference fallback behavior."""

import main


def test_java_backend_role_not_ai_operations():
    role = main._infer_target_role(
        "Java 后端开发实习生\n负责 Java 服务开发、数据库设计与接口联调"
    )
    assert role == "Java 后端开发实习生"
    assert role != "AI应用运营实习生"


def test_ai_app_development_role_recognized():
    role = main._infer_target_role("AI应用开发实习生\n负责大模型应用开发与 Prompt 工程")
    assert role == "AI应用开发实习生"


def test_unrecognized_jd_returns_safe_fallback():
    role = main._infer_target_role("负责日常事务处理，整理文档，协助会议安排")
    assert role == "目标岗位"
    assert role != "AI应用运营实习生"


def test_empty_jd_returns_safe_fallback():
    assert main._infer_target_role("") == "目标岗位"


def test_explicit_target_role_wins_over_inference():
    assert (
        main._resolve_target_role(
            "数据运营实习生",
            "AI产品经理 负责需求分析与功能迭代",
        )
        == "数据运营实习生"
    )

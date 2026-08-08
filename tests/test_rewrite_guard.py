"""Unit tests for the lightweight rewrite fact-consistency guard."""

import pytest

from fact_guard import RewriteFactError, validate_rewrite_facts


def test_missing_email_fails():
    original = "张凡\nzhangfan@example.com\n项目经历"
    rewritten = "# 张凡\n项目经历\n- 完成需求分析"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_missing_phone_fails():
    original = "张凡\n13812345678\n项目经历"
    rewritten = "# 张凡\n项目经历"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_replaced_placeholder_name_fails():
    original = "测试候选人\n某大学\n杭州"
    rewritten = "# 张伟\n某大学\n杭州"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_replaced_placeholder_school_fails():
    original = "测试候选人\n某大学\n杭州"
    rewritten = "# 测试候选人\nXX大学\n杭州"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_replaced_city_fails():
    original = "测试候选人\n某大学\n杭州"
    rewritten = "# 测试候选人\n某大学\n北京"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_invented_fake_name_without_source_fails():
    original = "匿名简历\n项目经历"
    rewritten = "# 李雷\n项目经历"
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts(original, rewritten)


def test_preserved_contact_and_facts_pass():
    original = (
        "张凡\n138-0000-0000\nzhangfan@example.com\n"
        "https://github.com/zhangfan\n某大学\n杭州\n"
        "项目经历\n- 完成需求分析"
    )
    rewritten = (
        "# 张凡\n"
        "138-0000-0000 | zhangfan@example.com | 杭州\n"
        "[GitHub](https://github.com/zhangfan)\n"
        "某大学\n"
        "## 项目经历\n"
        "- 完成需求分析，按 STAR 法则重写表达"
    )
    validate_rewrite_facts(original, rewritten)  # should not raise


def test_empty_input_fails():
    with pytest.raises(RewriteFactError):
        validate_rewrite_facts("", "内容")

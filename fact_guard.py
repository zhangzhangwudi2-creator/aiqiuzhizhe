"""Lightweight fact-consistency guard for rewritten resumes.

This is a cheap safety net, not a full fact-checking system. It blocks the
most dangerous, easy-to-detect cases:

* contact details (email / phone / URL) present in the original resume
  disappearing from the rewritten resume;
* common fake names, placeholder schools, or placeholder cities appearing
  in the rewritten resume although they were absent from the original.

It deliberately avoids entity recognition, similarity scoring, and any
second LLM call.
"""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s)\]}>]+", re.IGNORECASE)

# Tokens that strongly suggest fabrication when they appear only in the
# rewritten resume. Real resumes that already contain them are unaffected,
# because the guard only flags tokens absent from the original text.
FAKE_NAME_TOKENS = (
    "张伟", "李雷", "王小明", "李明", "张三", "李四", "王五", "赵六",
    "张伟明", "王强",
)
FAKE_SCHOOL_TOKENS = (
    "XX大学", "xx大学", "某某大学", "北京大学", "清华大学", "浙江大学",
    "复旦大学", "上海交通大学", "南京大学", "武汉大学",
)
FAKE_CITY_TOKENS = (
    "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京",
    "西安", "重庆", "长沙",
)
HIGHLY_RISK_TOKENS = FAKE_NAME_TOKENS + FAKE_SCHOOL_TOKENS + FAKE_CITY_TOKENS


class RewriteFactError(ValueError):
    """Raised when a rewritten resume fails the fact-consistency check."""


def _phone_digits(text: str) -> set[str]:
    """Return 11-digit mobile numbers found in the digit stream of a text."""
    digits = re.sub(r"\D", "", text)
    return set(re.findall(r"(?<!\d)1[3-9]\d{9}(?!\d)", digits))


def validate_rewrite_facts(original_resume_text: str, rewritten_markdown: str) -> None:
    """Raise RewriteFactError if the rewrite drops or fabricates high-risk facts."""
    if not original_resume_text.strip() or not rewritten_markdown.strip():
        raise RewriteFactError("改写内容为空，无法进行事实一致性校验")

    original_lower = original_resume_text.lower()
    rewritten_lower = rewritten_markdown.lower()

    missing_contacts = []
    for item in {m.group(0).lower() for m in EMAIL_RE.finditer(original_lower)}:
        if item not in rewritten_lower:
            missing_contacts.append(f"邮箱 {item}")
    for item in {m.group(0).lower() for m in URL_RE.finditer(original_lower)}:
        if item not in rewritten_lower:
            missing_contacts.append(f"链接 {item}")
    for item in _phone_digits(original_lower):
        if item not in _phone_digits(rewritten_lower):
            missing_contacts.append(f"手机号 {item}")

    if missing_contacts:
        raise RewriteFactError(
            "改写结果丢失了原始简历中的联系方式：" + "、".join(sorted(missing_contacts))
        )

    invented = [
        token
        for token in HIGHLY_RISK_TOKENS
        if token in rewritten_lower and token not in original_lower
    ]
    if invented:
        raise RewriteFactError(
            "改写结果出现原始简历中不存在的高风险信息：" + "、".join(invented)
        )

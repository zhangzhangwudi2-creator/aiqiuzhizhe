"""Validated response contracts for model output."""

from typing import Literal

from pydantic import BaseModel, Field


class Strength(BaseModel):
    point: str = Field(min_length=1)
    detail: str = Field(min_length=1)


class SkillGap(BaseModel):
    skill: str = Field(min_length=1)
    importance: Literal["高", "中", "低"]
    current_status: str = Field(min_length=1)
    improvement_suggestion: str = Field(min_length=1)


class ResumeTip(BaseModel):
    section: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    rewrite_suggestion: str = Field(min_length=1)


class InterviewQuestion(BaseModel):
    question: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    difficulty: Literal["简单", "中等", "困难"]


class AnalysisResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    strengths: list[Strength] = Field(min_length=1)
    skill_gaps: list[SkillGap] = Field(min_length=1)
    resume_tips: list[ResumeTip] = Field(min_length=1)
    interview_questions: list[InterviewQuestion] = Field(min_length=1)

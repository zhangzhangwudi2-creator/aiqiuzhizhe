"""
简历模型 - 管理用户简历信息
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Resume(BaseModel):
    id: Optional[int] = None
    user_id: int
    title: str = "我的简历"
    # 基本信息
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    title_summary: str = ""  # 一句话自我介绍
    # 详细内容 (JSON 结构化存储)
    summary: str = ""        # 个人总结
    education: list[dict] = []      # 教育经历
    experience: list[dict] = []     # 工作经历
    projects: list[dict] = []      # 项目经验
    skills: list[str] = []         # 技能列表
    certifications: list[dict] = [] # 证书
    languages: list[dict] = []     # 语言能力
    # 原始文件
    original_filename: str = ""
    file_path: str = ""
    parsed_text: str = ""
    # 元数据
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class ResumeAnalysis(BaseModel):
    """AI 简历分析结果"""
    resume_id: int
    overall_score: float           # 综合评分 0-100
    strengths: list[str]           # 优势
    weaknesses: list[str]          # 不足
    suggestions: list[str]         # 改进建议
    keywords_match: dict           # 关键词匹配情况
    format_score: float            # 格式评分
    content_score: float           # 内容评分
    relevance_score: float         # 岗位匹配度评分
    analyzed_at: datetime = datetime.now()

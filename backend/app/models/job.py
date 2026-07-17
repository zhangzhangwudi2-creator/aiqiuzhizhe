"""
职位模型 - 管理招聘信息和职位匹配
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Job(BaseModel):
    id: Optional[int] = None
    title: str                     # 职位名称
    company: str                   # 公司名称
    location: str = ""             # 工作地点
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "CNY"
    description: str = ""          # 职位描述
    requirements: list[str] = []   # 任职要求
    responsibilities: list[str] = [] # 岗位职责
    benefits: list[str] = []       # 福利待遇
    industry: str = ""             # 行业
    job_type: str = "全职"         # 全职/兼职/实习
    experience_level: str = ""     # 经验要求
    education_level: str = ""      # 学历要求
    source: str = ""               # 来源（手动/爬取/API）
    source_url: str = ""           # 来源链接
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class JobMatch(BaseModel):
    """职位匹配结果"""
    job_id: int
    resume_id: int
    match_score: float             # 匹配度 0-100
    skill_match: dict              # 技能匹配详情
    experience_match: dict         # 经验匹配详情
    education_match: dict          # 学历匹配详情
    missing_skills: list[str]      # 缺失的技能
    recommended_actions: list[str] # 建议行动
    ai_comment: str                # AI 综合评语
    matched_at: datetime = datetime.now()

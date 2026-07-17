# -*- coding: utf-8 -*-
"""
AI 服务 - 对接 OpenAI / DeepSeek API 提供智能功能
支持双 API 提供商，优先使用 DeepSeek，其次 OpenAI，兜底模拟模式
"""
import json
from typing import Optional, Literal
from datetime import datetime

from ..config import settings


class AIService:
    """AI 服务封装，提供简历分析、优化、职位匹配等功能"""

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.deepseek_api_key = settings.DEEPSEEK_API_KEY
        self.deepseek_model = settings.DEEPSEEK_MODEL
        self.deepseek_base_url = settings.DEEPSEEK_BASE_URL
        self._client = None
        self._provider = "mock"

    async def _get_client(self):
        if self._client is not None:
            return self._client
        if self.deepseek_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.deepseek_api_key, base_url=self.deepseek_base_url)
                self._provider = "deepseek"
                return self._client
            except ImportError:
                pass
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.openai_api_key)
                self._provider = "openai"
                return self._client
            except ImportError:
                pass
        return None

    def _get_model(self) -> str:
        if self._provider == "deepseek":
            return self.deepseek_model
        return self.openai_model

    async def _call_chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7):
        client = await self._get_client()
        if client and self._provider != "mock":
            try:
                response = await client.chat.completions.create(
                    model=self._get_model(),
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                return json.loads(response.choices[0].message.content)
            except Exception:
                pass
        return None

    async def analyze_resume(self, resume, job_description: str = "") -> dict:
        result = await self._call_chat(system_prompt="你是一位专业的简历顾问，精通简历优化和求职指导。", user_prompt=self._build_analysis_prompt(resume, job_description))
        if result:
            result["analyzed_at"] = datetime.now()
            return result
        return self._mock_analysis(resume, job_description)

    async def optimize_resume(self, resume, job_description: str = "") -> dict:
        result = await self._call_chat(system_prompt="你是一位专业的简历优化专家。", user_prompt=self._build_optimize_prompt(resume, job_description))
        if result:
            return result
        return self._mock_optimization(resume, job_description)

    async def match_job_resume(self, job, resume_id: int) -> dict:
        result = await self._call_chat(system_prompt="你是一位招聘专家，擅长评估人岗匹配度。", user_prompt=self._build_match_prompt(job, resume_id), temperature=0.5)
        if result:
            return result
        return self._mock_match(job, resume_id)

    def _build_analysis_prompt(self, resume, job_description: str) -> str:
        skills_str = ", ".join(resume.skills)
        job_str = job_description if job_description else "无特定目标"
        return f"""请分析以下简历内容，给出专业评估：
简历信息：
- 姓名：{resume.full_name}
- 技能：{skills_str}
- 个人总结：{resume.summary}
- 教育经历：{json.dumps(resume.education, ensure_ascii=False)}
- 工作经历：{json.dumps(resume.experience, ensure_ascii=False)}
- 项目经验：{json.dumps(resume.projects, ensure_ascii=False)}
目标职位描述：{job_str}
返回 JSON 结构：
{{"overall_score": float, "strengths": [str], "weaknesses": [str], "suggestions": [str], "keywords_match": {{}}, "format_score": float, "content_score": float, "relevance_score": float}}"""

    def _build_optimize_prompt(self, resume, job_description: str) -> str:
        skills_str = ", ".join(resume.skills)
        job_str = job_description if job_description else "无特定目标"
        return f"""请优化以下简历：
简历信息：
- 姓名：{resume.full_name}
- 技能：{skills_str}
- 个人总结：{resume.summary}
- 教育经历：{json.dumps(resume.education, ensure_ascii=False)}
- 工作经历：{json.dumps(resume.experience, ensure_ascii=False)}
- 项目经验：{json.dumps(resume.projects, ensure_ascii=False)}
目标职位：{job_str}
返回 JSON 结构：
{{"optimized_summary": str, "optimized_experience": [{{}}], "changes": [str]}}"""

    def _build_match_prompt(self, job, resume_id: int) -> str:
        return f"""请分析以下职位与简历的匹配度：
职位信息：
- 职位名称：{job.title}
- 公司：{job.company}
- 要求：{job.requirements}
- 描述：{job.description}
简历 ID：{resume_id}
返回 JSON 结构：
{{"match_score": float, "skill_match": {{}}, "experience_match": {{}}, "education_match": {{}}, "missing_skills": [str], "recommended_actions": [str], "ai_comment": str}}"""

    def _mock_analysis(self, resume, job_description: str) -> dict:
        return {"overall_score": 75.0, "strengths": ["技能覆盖面广", "项目经验丰富", "结构清晰"], "weaknesses": ["缺乏量化成果描述", "个人总结不够突出核心优势"], "suggestions": ["在项目经历中加入具体数据指标", "针对目标职位调整关键词", "补充专业技能证书信息"], "keywords_match": {"matched": ["Python", "项目管理"], "missing": ["团队管理"]}, "format_score": 80.0, "content_score": 70.0, "relevance_score": 75.0}

    def _mock_optimization(self, resume, job_description: str) -> dict:
        return {"optimized_summary": f"拥有{len(resume.skills)}项核心技能的专业人士...", "optimized_experience": resume.experience, "changes": ["优化了个人总结", "突出了量化成果"]}

    def _mock_match(self, job, resume_id: int) -> dict:
        return {"job_id": job.id, "resume_id": resume_id, "match_score": 82.0, "skill_match": {"matched": ["Python", "数据分析"], "partial": ["AI"], "missing": ["Docker"]}, "experience_match": {"relevant_years": 3, "required_years": 3}, "education_match": {"match": True}, "missing_skills": ["Docker", "Kubernetes"], "recommended_actions": ["补充云原生相关经验", "学习 Docker 容器化技术"], "ai_comment": "候选人的技术背景与岗位要求高度匹配，建议补充云原生领域经验。"}
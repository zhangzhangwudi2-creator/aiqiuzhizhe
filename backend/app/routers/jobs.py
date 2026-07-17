"""
职位路由 - 职位搜索、匹配、推荐
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.job import Job, JobMatch
from ..services.ai_service import AIService

router = APIRouter(prefix="/api/jobs", tags=["职位"])

# 模拟存储
_jobs_db: dict[int, Job] = {}
_matches_db: dict[int, JobMatch] = {}
_next_job_id: int = 1


@router.post("/", response_model=Job)
async def create_job(job: Job):
    """手动创建职位"""
    global _next_job_id
    job.id = _next_job_id
    _jobs_db[_next_job_id] = job
    _next_job_id += 1
    return job


@router.get("/")
async def search_jobs(
    keyword: Optional[str] = Query("", description="搜索关键词"),
    location: Optional[str] = Query("", description="工作地点"),
    job_type: Optional[str] = Query("", description="工作类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """搜索职位"""
    results = []
    for job in _jobs_db.values():
        if keyword and keyword.lower() not in job.title.lower() and \
           keyword.lower() not in job.description.lower():
            continue
        if location and location.lower() not in job.location.lower():
            continue
        if job_type and job_type != job.job_type:
            continue
        results.append(job)
    
    # 分页
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]
    
    return {
        "jobs": page_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: int):
    """获取职位详情"""
    if job_id not in _jobs_db:
        raise HTTPException(status_code=404, detail="职位不存在")
    return _jobs_db[job_id]


@router.post("/{job_id}/match/{resume_id}", response_model=JobMatch)
async def match_job(job_id: int, resume_id: int):
    """AI 匹配职位与简历"""
    if job_id not in _jobs_db:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    # 这里需要从 resumes 路由获取简历数据
    # 简化处理：直接调用 AI 服务
    job = _jobs_db[job_id]
    ai_service = AIService()
    match = await ai_service.match_job_resume(job, resume_id)
    
    _matches_db[f"{job_id}_{resume_id}"] = match
    return match


@router.get("/recommendations/{resume_id}")
async def get_recommendations(resume_id: int):
    """基于简历获取职位推荐"""
    # 简化的推荐：返回所有职位并按匹配度排序
    ai_service = AIService()
    recommendations = []
    
    for job in _jobs_db.values():
        match = await ai_service.match_job_resume(job, resume_id)
        if match.match_score >= 60:  # 只返回匹配度 >= 60 的职位
            recommendations.append({
                "job": job,
                "match_score": match.match_score,
                "missing_skills": match.missing_skills,
            })
    
    # 按匹配度降序排列
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {"recommendations": recommendations, "total": len(recommendations)}

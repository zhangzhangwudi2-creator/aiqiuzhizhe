"""
简历路由 - 上传、解析、分析、优化简历
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional

from ..models.resume import Resume, ResumeAnalysis
from ..services.resume_parser import ResumeParser
from ..services.ai_service import AIService
from ..utils.helpers import FileManager

router = APIRouter(prefix="/api/resumes", tags=["简历"])

# 模拟存储
_resumes_db: dict[int, Resume] = {}
_analysis_db: dict[int, ResumeAnalysis] = {}
_next_id: int = 1


@router.post("/upload", response_model=Resume)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    title: Optional[str] = Form("我的简历"),
):
    """上传并解析简历文件（PDF/Word）"""
    global _next_id

    # 验证文件类型
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 Word 文档格式")

    # 验证文件大小
    content = await file.read()
    from ..config import settings
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB）")

    # 保存文件到磁盘
    file_path = FileManager.save_upload(content, file.filename)

    # 解析简历
    parser = ResumeParser()
    try:
        parsed = await parser.parse(content, file.filename, file.content_type)
    except Exception as e:
        # 解析失败时删除已保存的文件
        FileManager.delete_file(file_path)
        raise HTTPException(status_code=422, detail=f"简历解析失败: {str(e)}")

    resume = Resume(
        id=_next_id,
        user_id=user_id,
        title=title,
        full_name=parsed.get("full_name", ""),
        email=parsed.get("email", ""),
        phone=parsed.get("phone", ""),
        location=parsed.get("location", ""),
        title_summary=parsed.get("title_summary", ""),
        summary=parsed.get("summary", ""),
        skills=parsed.get("skills", []),
        education=parsed.get("education", []),
        experience=parsed.get("experience", []),
        projects=parsed.get("projects", []),
        certifications=parsed.get("certifications", []),
        languages=parsed.get("languages", []),
        original_filename=file.filename,
        file_path=file_path,
        parsed_text=parsed.get("raw_text", ""),
    )

    _resumes_db[_next_id] = resume
    _next_id += 1

    return resume


@router.get("/{resume_id}", response_model=Resume)
async def get_resume(resume_id: int):
    """获取简历详情"""
    if resume_id not in _resumes_db:
        raise HTTPException(status_code=404, detail="简历不存在")
    return _resumes_db[resume_id]


@router.get("/user/{user_id}")
async def list_user_resumes(user_id: int):
    """获取用户所有简历"""
    resumes = [r for r in _resumes_db.values() if r.user_id == user_id]
    return {"resumes": resumes, "total": len(resumes)}


@router.delete("/{resume_id}")
async def delete_resume(resume_id: int):
    """删除简历"""
    if resume_id not in _resumes_db:
        raise HTTPException(status_code=404, detail="简历不存在")

    resume = _resumes_db[resume_id]
    if resume.file_path:
        FileManager.delete_file(resume.file_path)
    del _resumes_db[resume_id]
    if resume_id in _analysis_db:
        del _analysis_db[resume_id]

    return {"message": "简历已删除", "resume_id": resume_id}


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysis)
async def analyze_resume(resume_id: int, job_description: Optional[str] = ""):
    """AI 分析简历，可选传入目标职位描述"""
    if resume_id not in _resumes_db:
        raise HTTPException(status_code=404, detail="简历不存在")

    resume = _resumes_db[resume_id]
    ai_service = AIService()
    analysis = await ai_service.analyze_resume(resume, job_description)

    _analysis_db[resume_id] = analysis
    return analysis


@router.put("/{resume_id}/optimize")
async def optimize_resume(resume_id: int, job_description: str = ""):
    """AI 优化简历内容"""
    if resume_id not in _resumes_db:
        raise HTTPException(status_code=404, detail="简历不存在")

    resume = _resumes_db[resume_id]
    ai_service = AIService()
    optimized = await ai_service.optimize_resume(resume, job_description)

    return {"optimized_content": optimized, "resume_id": resume_id}

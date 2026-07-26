"""FastAPI backend for the AI resume assistant."""

import asyncio
import io
import json
import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pypdf import PdfReader

from prompts import REWRITE_PROMPT, SYSTEM_PROMPT, build_prompt, build_rewrite_prompt
from quota import SlidingWindowRateLimiter, TTLCache, build_cache_key
from schemas import AnalysisResult
from pdf_resume import PhotoNotFoundError, build_resume_pdf, extract_profile_photo

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_RESUME_CHARS = 30_000
MAX_JD_CHARS = 15_000
MAX_TARGET_ROLE_CHARS = 60
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "21600"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))

response_cache = TTLCache(max_entries=100, ttl_seconds=CACHE_TTL_SECONDS)
rate_limiter = SlidingWindowRateLimiter(
    max_requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "").strip()
    if not configured:
        return []
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app = FastAPI(title="AI 求职助手", version="1.2.0")

allowed_origins = _cors_origins()
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="AI 服务尚未配置，请联系管理员")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=60.0,
        max_retries=1,
    )


@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


def _extract_pdf_text(contents: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(contents))
        text = "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PDF 解析失败，请确认文件未损坏") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="无法从 PDF 中提取文字，请使用文字版简历")
    return text[:MAX_RESUME_CHARS]


async def _parse_resume(resume: UploadFile) -> str:
    filename = resume.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 格式的简历")
    if resume.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="文件类型不是 PDF")

    contents = await resume.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF 文件不能超过 10MB")
    return await asyncio.to_thread(_extract_pdf_text, contents)


async def _read_resume_pdf(resume: UploadFile) -> bytes:
    filename = resume.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 格式的简历")
    if resume.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="文件类型不是 PDF")
    contents = await resume.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF 文件不能超过 10MB")
    return contents


def _validate_jd(jd_text: str) -> str:
    cleaned = jd_text.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="请输入岗位描述")
    if len(cleaned) > MAX_JD_CHARS:
        raise HTTPException(status_code=413, detail="岗位描述不能超过 15000 字")
    return cleaned


def _validate_target_role(target_role: str) -> str:
    cleaned = target_role.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="请输入目标岗位名称")
    if len(cleaned) > MAX_TARGET_ROLE_CHARS:
        raise HTTPException(status_code=413, detail="目标岗位名称不能超过 60 字")
    return cleaned


def _client_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request) -> None:
    allowed, retry_after = rate_limiter.check(_client_identity(request))
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": str(retry_after)},
        )


async def _chat_completion(*, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int, json_output: bool = False) -> str:
    client = _get_client()
    request = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_output:
        request["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后重试") from exc

    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="AI 服务返回了空内容，请重试")
    return content


@app.post("/analyze")
async def analyze(request: Request, resume: UploadFile = File(...), jd_text: str = Form(...)):
    resume_text = await _parse_resume(resume)
    jd = _validate_jd(jd_text)
    cache_key = build_cache_key("analyze", resume_text, jd)
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached
    _enforce_rate_limit(request)
    content = await _chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_prompt(resume_text, jd),
        temperature=0.3,
        max_tokens=4096,
        json_output=True,
    )
    try:
        result = AnalysisResult.model_validate_json(content).model_dump()
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请重试") from exc
    response_cache.set(cache_key, result)
    return result


@app.post("/rewrite-resume")
async def rewrite_resume(
    request: Request,
    resume: UploadFile = File(...),
    jd_text: str = Form(...),
    target_role: str = Form(...),
):
    resume_text = await _parse_resume(resume)
    jd = _validate_jd(jd_text)
    role = _validate_target_role(target_role)
    cache_key = build_cache_key("rewrite", resume_text, f"{role}\n{jd}")
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached
    _enforce_rate_limit(request)
    content = await _chat_completion(
        system_prompt=REWRITE_PROMPT,
        user_prompt=build_rewrite_prompt(resume_text, jd, role),
        temperature=0.35,
        max_tokens=8192,
    )
    result = {"target_role": role, "rewritten_resume": content}
    response_cache.set(cache_key, result)
    return result


@app.post("/export-resume-pdf")
async def export_resume_pdf(
    resume: UploadFile = File(...),
    rewritten_resume: str = Form(...),
    target_role: str = Form(...),
):
    """Export a real PDF and refuse to silently drop the source photo."""
    contents = await _read_resume_pdf(resume)
    role = _validate_target_role(target_role)
    text = rewritten_resume.strip()
    if not text:
        raise HTTPException(status_code=400, detail="请先生成优化简历")
    if len(text) > MAX_RESUME_CHARS:
        raise HTTPException(status_code=413, detail="优化简历内容不能超过 30000 字")
    try:
        photo = await asyncio.to_thread(extract_profile_photo, contents)
        pdf = await asyncio.to_thread(build_resume_pdf, text, photo, role)
    except PhotoNotFoundError as exc:
        raise HTTPException(
            status_code=422,
            detail="原 PDF 中未检测到可提取的照片，已停止导出，避免生成无照片简历。请上传带内嵌证件照的 PDF。",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PDF 生成失败，请确认原简历文件完整") from exc

    safe_name = "".join("_" if c in '\\/:*?\"<>|' else c for c in role)
    filename = f"{safe_name}_针对性简历.pdf"
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "no-store",
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "ai_configured": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
        "rate_limit": f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW_SECONDS}s",
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

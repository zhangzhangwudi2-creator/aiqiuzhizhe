"""
AI求职助手 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import auth_router, resume_router, jobs_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 驱动的智能求职助手后端服务",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(jobs_router)


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """根路径重定向到前端"""
    return {
        "message": "欢迎使用 AI求职助手 API",
        "docs": "/api/docs",
        "frontend": "/static/index.html",
    }


# 确保上传目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

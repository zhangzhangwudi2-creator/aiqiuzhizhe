# backend/app/routers/__init__.py
from .auth import router as auth_router
from .resume import router as resume_router
from .jobs import router as jobs_router

__all__ = ["auth_router", "resume_router", "jobs_router"]

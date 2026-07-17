"""
认证路由 - 用户注册、登录、Token 管理
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..models.user import UserCreate, UserLogin, UserResponse
from ..utils.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# 模拟用户存储（后续替换为数据库）
_fake_users_db: dict = {}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """用户注册"""
    if user.username in _fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    hashed = get_password_hash(user.password)
    user_id = len(_fake_users_db) + 1
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
        "full_name": user.full_name,
        "is_active": True,
    }
    _fake_users_db[user.username] = new_user
    
    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name or "",
        is_active=True,
        created_at=new_user.get("created_at"),
    )


@router.post("/login")
async def login(user: UserLogin):
    """用户登录，返回 JWT Token"""
    db_user = _fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": db_user["id"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user["id"],
        "username": db_user["username"],
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户信息"""
    payload = decode_token(token)
    username = payload.get("sub")
    if username not in _fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    user = _fake_users_db[username]
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        is_active=user["is_active"],
        created_at=user.get("created_at"),
    )

"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.auth_service import AuthService
from app.api.deps import get_current_user


router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    username: str
    password: str
    domain: str = None


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: dict


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    email: str
    username: str
    domain: str


@router.post("/register")
def register(req: RegisterRequest):
    """用户注册"""
    result = AuthService.register(
        email=req.email,
        username=req.username,
        password=req.password,
        domain=req.domain
    )
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result["message"]
    )


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """用户登录"""
    result = AuthService.login(req.email, req.password)
    if result["success"]:
        return LoginResponse(**result["data"])
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=result["message"]
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(**current_user)


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """退出登录"""
    return {"success": True, "message": "已退出登录"}
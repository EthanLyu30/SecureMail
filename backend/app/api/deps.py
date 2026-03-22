"""
API依赖项
"""
from typing import Optional
from fastapi import Header, HTTPException, status, Depends

from app.services import AuthService


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """获取当前用户"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权"
        )

    # 解析 Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证方案"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证头"
        )

    # 验证 token
    user_data = AuthService.validate_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期或无效"
        )

    return user_data
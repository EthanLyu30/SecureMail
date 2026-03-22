"""
FastAPI 主应用 - 支持多域名部署
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings, update_settings_from_env
from app.models import init_db
from app.api import auth_router, mail_router, group_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动前 - 更新配置
    update_settings_from_env()
    
    print("=" * 50)
    print(f"正在启动 {settings.APP_NAME} ...")
    print(f"域名: {settings.DOMAIN_NAME}")
    print(f"端口: {settings.PORT}")
    print(f"数据库: {settings.DATABASE_URL}")
    print("=" * 50)
    
    # 初始化数据库
    init_db()
    print(f"应用启动完成，监听 {settings.HOST}:{settings.PORT}")
    
    yield
    
    print("正在关闭应用...")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(mail_router, prefix="/api")
app.include_router(group_router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "domain": settings.DOMAIN_NAME
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "domain": settings.DOMAIN_NAME,
        "port": settings.PORT
    }


@app.get("/api/domain/info")
async def domain_info():
    """获取域名信息"""
    return {
        "domain": settings.DOMAIN_NAME,
        "domain_id": settings.DOMAIN_ID,
        "relay_enabled": settings.RELAY_ENABLED,
        "other_domains": settings.OTHER_DOMAINS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
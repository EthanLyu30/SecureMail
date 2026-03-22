"""
核心配置模块
"""
import os
from typing import Optional
from pydantic import BaseModel
from functools import lru_cache


class Settings(BaseModel):
    """应用配置"""
    # 应用
    APP_NAME: str = "智能安全邮箱"
    APP_NAME_EN: str = "SecureMail"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器 - 支持多域名部署
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 域名配置
    DOMAIN_NAME: str = "example.com"
    DOMAIN_ID: int = 1
    
    # 数据目录 - 支持逻辑隔离
    DATA_DIR: str = "/home/exam/backend/data"

    # 数据库
    DATABASE_URL: str = "sqlite:///./mail.db"

    # JWT
    SECRET_KEY: str = "secure-mail-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 60  # 30分钟

    # 安全
    PASSWORD_MIN_LENGTH: int = 6
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 30
    SEND_RATE_LIMIT: int = 20  # 每分钟发送上限

    # 邮件
    MAX_ATTACHMENT_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_ATTACHMENT_TYPES: list = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/zip",
        "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    # 服务器间通信 - 用于跨域邮件
    RELAY_ENABLED: bool = True
    RELAY_HOST: str = "localhost"
    RELAY_PORT: int = 8001  # 默认中继端口
    
    # 其他域名服务器配置
    OTHER_DOMAINS: str = "test.com:8002"  # 格式: domain:port

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # 存储
    ATTACHMENT_DIR: str = "/home/exam/backend/data/attachments"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()

# 根据环境变量动态设置
def update_settings_from_env():
    """从环境变量更新配置"""
    global settings
    
    if os.getenv("DOMAIN_NAME"):
        settings.DOMAIN_NAME = os.getenv("DOMAIN_NAME")
    if os.getenv("DOMAIN_ID"):
        settings.DOMAIN_ID = int(os.getenv("DOMAIN_ID"))
    if os.getenv("SERVER_PORT"):
        settings.PORT = int(os.getenv("SERVER_PORT"))
    if os.getenv("DATA_DIR"):
        settings.DATA_DIR = os.getenv("DATA_DIR")
    if os.getenv("ATTACHMENT_DIR"):
        settings.ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR")
    if os.getenv("RELAY_PORT"):
        settings.RELAY_PORT = int(os.getenv("RELAY_PORT"))
    if os.getenv("OTHER_DOMAINS"):
        settings.OTHER_DOMAINS = os.getenv("OTHER_DOMAINS")
        
    # 更新数据库路径
    if settings.DOMAIN_NAME:
        db_path = f"./{settings.DOMAIN_NAME.replace('.', '_')}_mail.db"
        settings.DATABASE_URL = f"sqlite:///{db_path}"
        
    return settings
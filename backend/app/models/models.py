"""
数据库模型定义
使用 SQLAlchemy 同步模式 + SQLite（开发测试）
PostgreSQL 作为生产数据库
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, Enum as SQLEnum, JSON, create_engine
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

# 创建基类
Base = declarative_base()

# 枚举类型
import enum


class EmailFolder(enum.Enum):
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class Domain(Base):
    """域名表 - 支持多域名部署"""
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)

    # 安全字段
    failed_login_attempts = Column(Integer, default=0)
    lock_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)

    # 外键
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class Group(Base):
    """群组表"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupMember(Base):
    """群组成员表"""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    created_at = Column(DateTime, default=datetime.utcnow)


class Email(Base):
    """邮件表"""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mail_uuid = Column(String(36), unique=True, nullable=False, index=True)
    subject = Column(String(500), default="")
    body = Column(Text, default="")

    # 关键词和分类
    keywords = Column(JSON)  # SQLite 用 JSON
    is_spam = Column(Boolean, default=False)
    is_phishing = Column(Boolean, default=False)
    phishing_score = Column(Integer, default=0)

    # 撤回标记
    is_recalled = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    recalled_at = Column(DateTime, nullable=True)

    # 发件人
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_email = Column(String(255), nullable=False)

    # 域
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailRecipient(Base):
    """邮件收件人表"""
    __tablename__ = "email_recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    recipient_type = Column(String(10), default="to")
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    folder = Column(String(20), default="inbox")
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailAttachment(Base):
    """邮件附件表"""
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size = Column(Integer, nullable=False)
    file_id = Column(String(64), unique=True, nullable=False, index=True)
    storage_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginAttempt(Base):
    """登录尝试记录表"""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    success = Column(Boolean, default=False)
    attempt_at = Column(DateTime, default=datetime.utcnow)


class SendRateLimit(Base):
    """发送频率限制表"""
    __tablename__ = "send_rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=False)
    window_minutes = Column(Integer, default=1)


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100))
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


# 数据库会话管理
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    # 创建默认域名
    db = SessionLocal()
    try:
        if not db.query(Domain).first():
            db.add(Domain(domain="example.com", description="默认域名"))
            db.add(Domain(domain="test.com", description="测试域名"))
            db.commit()
    finally:
        db.close()
"""
认证服务 - 同步版本
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re

from app.models import User, UserSession, LoginAttempt, Domain, SessionLocal
from app.core.security import SecurityManager
from app.core.config import settings


class AuthService:
    """认证服务"""

    @staticmethod
    def register(email: str, username: str, password: str, domain: str = None) -> dict:
        """用户注册

        Args:
            email: 完整邮箱地址
            username: 用户名
            password: 密码
            domain: 域名（可选，从email中提取）

        Returns:
            包含success, message, data的字典
        """
        db = SessionLocal()
        try:
            # 检查密码长度
            if len(password) < settings.PASSWORD_MIN_LENGTH:
                return {"success": False, "message": f"密码长度至少 {settings.PASSWORD_MIN_LENGTH} 位", "data": None}

            # 解析邮箱获取域名
            if domain is None and "@" in email:
                domain = email.split("@")[1]

            if not domain:
                return {"success": False, "message": "域名不能为空", "data": None}

            # 获取或创建域
            domain_obj = db.query(Domain).filter(Domain.domain == domain).first()
            if not domain_obj:
                domain_obj = Domain(domain=domain)
                db.add(domain_obj)
                db.commit()
                db.refresh(domain_obj)

            # 检查用户名是否存在
            existing = db.query(User).filter(
                User.username == username,
                User.domain_id == domain_obj.id
            ).first()

            if existing:
                return {"success": False, "message": "用户名已存在", "data": None}

            # 检查邮箱是否已存在
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return {"success": False, "message": "邮箱已被注册", "data": None}

            # 创建用户
            salt = SecurityManager.generate_salt()
            password_hash = SecurityManager.hash_password(password, salt)

            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                domain_id=domain_obj.id
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return {
                "success": True,
                "message": "注册成功",
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "domain": domain
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"注册失败: {str(e)}", "data": None}
        finally:
            db.close()

    @staticmethod
    def login(email: str, password: str, ip_address: str = "") -> dict:
        """用户登录

        Args:
            email: 邮箱地址或用户名@域名
            password: 密码
            ip_address: IP地址

        Returns:
            包含success, message, data的字典
        """
        db = SessionLocal()
        try:
            # 优先通过完整邮箱查找用户
            user = db.query(User).filter(User.email == email).first()
            username = email  # 用于日志记录

            if not user:
                # 如果不是完整邮箱，尝试解析
                if "@" in email:
                    username, domain_str = email.split("@", 1)
                else:
                    username = email
                    domain_str = settings.DEFAULT_DOMAIN

                # 获取域
                domain = db.query(Domain).filter(Domain.domain == domain_str).first()
                if not domain:
                    return {"success": False, "message": "域名无效", "data": None}

                # 获取用户
                user = db.query(User).filter(
                    User.username == username,
                    User.domain_id == domain.id
                ).first()

            if not user:
                # 记录失败尝试
                attempt = LoginAttempt(username=username, ip_address=ip_address, success=False)
                db.add(attempt)
                db.commit()
                return {"success": False, "message": "用户不存在", "data": None}

            # 获取域名
            domain = db.query(Domain).filter(Domain.id == user.domain_id).first()

            # 检查登录是否允许
            lock_until = user.lock_until
            if lock_until and datetime.utcnow() < lock_until:
                remaining = (lock_until - datetime.utcnow()).seconds // 60
                attempt = LoginAttempt(username=username, ip_address=ip_address, success=False)
                db.add(attempt)
                db.commit()
                return {"success": False, "message": f"账户已被锁定，请 {remaining} 分钟后重试", "data": None}

            if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                attempt = LoginAttempt(username=username, ip_address=ip_address, success=False)
                db.add(attempt)
                db.commit()
                return {"success": False, "message": "登录尝试过于频繁，请稍后再试", "data": None}

            # 验证密码
            if not SecurityManager.verify_password(password, user.salt, user.password_hash):
                # 记录失败
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                    user.lock_until = SecurityManager.calculate_lock_time(user.failed_login_attempts)
                user.lock_until = None
                db.commit()

                attempt = LoginAttempt(username=username, ip_address=ip_address, success=False)
                db.add(attempt)
                db.commit()

                return {"success": False, "message": "密码错误", "data": None}

            # 登录成功
            user.failed_login_attempts = 0
            user.lock_until = None
            user.last_login_at = datetime.utcnow()
            db.commit()

            attempt = LoginAttempt(username=username, ip_address=ip_address, success=True)
            db.add(attempt)
            db.commit()

            # 创建会话
            import uuid
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

            session = UserSession(
                token=token,
                user_id=user.id,
                expires_at=expires_at,
                ip_address=ip_address
            )
            db.add(session)
            db.commit()

            return {
                "success": True,
                "message": "登录成功",
                "data": {
                    "token": token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "domain": domain.domain if domain else ""
                    }
                }
            }
        except Exception as e:
            return {"success": False, "message": f"登录失败: {str(e)}", "data": None}
        finally:
            db.close()

    @staticmethod
    def logout(token: str) -> bool:
        """登出"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(UserSession.token == token).first()
            if session:
                db.delete(session)
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def validate_token(token: str) -> Optional[dict]:
        """验证令牌"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.token == token,
                UserSession.expires_at > datetime.utcnow()
            ).first()

            if not session:
                return None

            user = db.query(User).filter(User.id == session.user_id).first()
            if not user:
                return None

            domain = db.query(Domain).filter(Domain.id == user.domain_id).first()

            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "domain_id": user.domain_id,
                "domain": domain.domain if domain else ""
            }
        finally:
            db.close()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """获取用户"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
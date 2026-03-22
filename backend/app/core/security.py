"""
安全模块 - 认证、授权、加密
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import secrets

from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings


# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """安全管理器"""

    # ==================== 密码相关 ====================

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """密码哈希（带盐值）"""
        salted = f"{password}{salt}"
        return hashlib.sha256(salted.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, salt: str, password_hash: str) -> bool:
        """验证密码"""
        return SecurityManager.hash_password(password, salt) == password_hash

    @staticmethod
    def generate_salt() -> str:
        """生成随机盐值"""
        return secrets.token_hex(16)

    @staticmethod
    def hash_password_bcrypt(password: str) -> str:
        """使用 bcrypt 哈希密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password_bcrypt(password: str, hashed: str) -> bool:
        """验证 bcrypt 密码"""
        return pwd_context.verify(password, hashed)

    # ==================== JWT Token ====================

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """解码访问令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    # ==================== 登录保护 ====================

    @staticmethod
    def check_login_allowed(failed_attempts: int, lock_until: Optional[datetime]) -> Tuple[bool, str]:
        """检查是否允许登录"""
        # 检查是否被锁定
        if lock_until and datetime.utcnow() < lock_until:
            remaining = (lock_until - datetime.utcnow()).seconds // 60
            return False, f"账户已被锁定，请 {remaining} 分钟后重试"

        # 检查尝试次数
        if failed_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            return False, "登录尝试过于频繁，请稍后再试"

        return True, ""

    @staticmethod
    def calculate_lock_time(failed_attempts: int) -> datetime:
        """计算锁定时间"""
        return datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)

    # ==================== 钓鱼检测 ====================

    @staticmethod
    def compute_phishing_score(subject: str, body: str) -> float:
        """计算钓鱼邮件分数"""
        score = 0.0
        phishing_keywords = [
            "urgent", "immediate action", "verify your account",
            "click here", "confirm your password", "bank account",
            "suspended", "unauthorized", "security alert",
            "限时", "立即行动", "验证账户", "点击此处",
            "确认密码", "银行账户", "已暂停", "安全警报"
        ]

        text = f"{subject} {body}".lower()
        for keyword in phishing_keywords:
            if keyword in text:
                score += 0.15

        # 短链接检测
        if "bit.ly" in text or "tinyurl" in text or "goo.gl" in text:
            score += 0.2

        # 异常大写字母检测
        upper_ratio = sum(1 for c in body if c.isupper()) / max(len(body), 1)
        if upper_ratio > 0.5:
            score += 0.15

        import re
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            if any(c.isdigit() for c in url) and "login" in url:
                score += 0.2

        is_phishing = score > 0.5
        return is_phishing, min(score, 1.0)

    # ==================== 关键词提取 ====================

    @staticmethod
    def extract_keywords(subject: str, body: str) -> list:
        """提取关键词"""
        import re
        from collections import Counter

        text = f"{subject} {body}".lower()
        words = re.findall(r'\b\w{3,}\b', text)

        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an',
            'to', 'of', 'in', 'for', 'with', 'this', 'that', 'from',
            'by', 'as', 'are', 'was', 'were', 'be', 'been', 'being'
        }

        keywords = [w for w in words if w not in stop_words]
        word_counts = Counter(keywords)

        return [word for word, count in word_counts.most_common(10)]

    # ==================== 文件去重 ====================

    @staticmethod
    def generate_file_id(content: bytes) -> str:
        """生成文件ID用于去重"""
        return hashlib.sha256(content).hexdigest()

    # ==================== 输入清理 ====================

    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """清理用户输入"""
        dangerous_chars = ['<', '>', '&', '"', "'", ';', '|', '`']
        sanitized = user_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized
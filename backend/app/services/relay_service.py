"""
跨域邮件中继服务
用于在不同域名服务器之间转发邮件
"""
import httpx
import asyncio
from typing import List, Optional
from app.core.config import settings
from app.models import Email, EmailRecipient, User, Domain, SessionLocal


class MailRelayService:
    """邮件中继服务 - 用于跨域名邮件发送"""
    
    @staticmethod
    def parse_other_domains() -> dict:
        """解析其他域名配置"""
        domains = {}
        if settings.OTHER_DOMAINS:
            for item in settings.OTHER_DOMAINS.split(","):
                item = item.strip()
                if ":" in item:
                    domain, port = item.split(":")
                    domains[domain] = int(port)
        return domains
    
    @staticmethod
    async def forward_to_domain(target_email: str, mail_data: dict) -> dict:
        """
        将邮件转发到目标域名服务器
        
        Args:
            target_email: 目标邮箱地址（如 user@test.com）
            mail_data: 邮件数据
            
        Returns:
            转发结果
        """
        # 解析目标邮箱的域名
        if "@" not in target_email:
            return {"success": False, "message": "无效的邮箱地址"}
        
        _, target_domain = target_email.split("@", 1)
        
        # 获取目标域名服务器地址
        other_domains = MailRelayService.parse_other_domains()
        
        if target_domain not in other_domains:
            # 目标是本域名，不需要中继
            return {"success": True, "message": "本域名邮件", "relayed": False}
        
        target_port = other_domains[target_domain]
        target_url = f"http://{settings.RELAY_HOST}:{target_port}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 调用目标服务器的API
                response = await client.post(
                    f"{target_url}/api/mail/relay/receive",
                    json=mail_data
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "邮件已转发", "relayed": True}
                else:
                    return {"success": False, "message": f"转发失败: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": f"转发异常: {str(e)}"}
    
    @staticmethod
    def receive_relay_mail(mail_data: dict) -> dict:
        """
        接收来自其他域名的邮件
        
        Args:
            mail_data: 邮件数据
            
        Returns:
            接收结果
        """
        db = SessionLocal()
        try:
            from app.services.mail_service import MailService
            
            # 解析邮件数据
            from_email = mail_data.get("from_email")
            to_addrs = mail_data.get("to_addrs", [])
            subject = mail_data.get("subject", "")
            body = mail_data.get("body", "")
            is_html = mail_data.get("is_html", False)
            
            if not from_email or not to_addrs:
                return {"success": False, "message": "邮件数据不完整"}
            
            # 获取发件人在本地域的账户
            sender = db.query(User).filter(User.email == from_email).first()
            if not sender:
                return {"success": False, "message": "发件人不存在"}
            
            # 发送邮件到本地用户
            result = MailService.send_email(
                user_id=sender.id,
                to_addrs=to_addrs,
                subject=subject,
                body=body,
                cc_addrs=mail_data.get("cc_addrs", []),
                bcc_addrs=mail_data.get("bcc_addrs", []),
                is_html=is_html
            )
            
            return result
        except Exception as e:
            return {"success": False, "message": f"接收邮件失败: {str(e)}"}
        finally:
            db.close()


# 同步版本用于API调用
class MailRelaySync:
    """同步邮件中继服务"""
    
    @staticmethod
    def forward_to_domain_sync(target_email: str, mail_data: dict) -> dict:
        """同步转发邮件"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                MailRelayService.forward_to_domain(target_email, mail_data)
            )
        finally:
            loop.close()
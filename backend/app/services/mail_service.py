"""
邮件服务 - 同步版本
"""
import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.models import (
    Email, EmailRecipient, EmailAttachment, Domain,
    User, SendRateLimit, SessionLocal
)
from app.core.security import SecurityManager
from app.core.config import settings


class MailService:
    """邮件服务"""

    @staticmethod
    def send_email(
        user_id: int,
        to_addrs: List[str],
        subject: str,
        body: str,
        cc_addrs: List[str] = None,
        bcc_addrs: List[str] = None,
        is_html: bool = False,
        is_draft: bool = False,
        attachments: List[dict] = None
    ) -> dict:
        """发送邮件

        Returns:
            包含success, message, data的字典
        """
        db = SessionLocal()
        try:
            # 如果是草稿，不检查频率限制
            if not is_draft:
                # 检查发送频率
                rate_limit_ok, rate_msg = MailService.check_send_rate(user_id)
                if not rate_limit_ok:
                    return {"success": False, "message": rate_msg, "data": None}

            # 获取发件人
            sender = db.query(User).filter(User.id == user_id).first()
            if not sender:
                return {"success": False, "message": "用户不存在", "data": None}

            # 获取域
            domain = db.query(Domain).filter(Domain.id == sender.domain_id).first()
            if not domain:
                return {"success": False, "message": "域名无效", "data": None}

            # 创建邮件
            mail_uuid = str(uuid.uuid4())

            # 关键词提取
            keywords = SecurityManager.extract_keywords(subject, body)

            # 钓鱼检测
            is_phishing, phishing_score = SecurityManager.compute_phishing_score(subject, body)

            # 创建邮件记录
            email = Email(
                mail_uuid=mail_uuid,
                subject=subject,
                body=body,
                from_user_id=sender.id,
                from_email=sender.email,
                domain_id=domain.id,
                keywords=keywords,
                is_phishing=is_phishing,
                phishing_score=int(phishing_score * 100),
                is_draft=is_draft
            )
            db.add(email)
            db.commit()
            db.refresh(email)

            # 处理附件
            for att_data in (attachments or []):
                file_data = base64.b64decode(att_data.get('data', ''))
                file_id = SecurityManager.generate_file_id(file_data)

                # 保存文件
                storage_path = os.path.join(settings.ATTACHMENT_DIR, file_id)
                os.makedirs(os.path.dirname(storage_path), exist_ok=True)

                with open(storage_path, 'wb') as f:
                    f.write(file_data)

                att = EmailAttachment(
                    email_id=email.id,
                    filename=att_data.get('filename', ''),
                    content_type=att_data.get('content_type', 'application/octet-stream'),
                    size=len(file_data),
                    file_id=file_id,
                    storage_path=storage_path
                )
                db.add(att)

            # 如果不是草稿，创建收件人记录
            if not is_draft:
                all_recipients = []
                all_recipients.extend(to_addrs or [])
                all_recipients.extend(cc_addrs or [])
                all_recipients.extend(bcc_addrs or [])

                for recipient_email in all_recipients:
                    recipient_user = db.query(User).filter(User.email == recipient_email).first()
                    if recipient_user:
                        rec = EmailRecipient(
                            email_id=email.id,
                            user_id=recipient_user.id,
                            recipient_type='to' if recipient_email in (to_addrs or []) else ('cc' if recipient_email in (cc_addrs or []) else 'bcc')
                        )
                        db.add(rec)

                # 记录发送次数
                MailService.record_send(user_id)

            db.commit()

            return {"success": True, "message": "邮件已发送", "data": {"mail_id": mail_uuid}}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e), "data": None}
        finally:
            db.close()

    @staticmethod
    def check_send_rate(user_id: int) -> Tuple[bool, str]:
        """检查发送频率"""
        now = datetime.utcnow()

        db = SessionLocal()
        try:
            rate_limit = db.query(SendRateLimit).filter(SendRateLimit.user_id == user_id).first()

            if not rate_limit:
                rate_limit = SendRateLimit(
                    user_id=user_id,
                    count=1,
                    window_start=now
                )
                db.add(rate_limit)
                db.commit()
                return True, ""

            # 检查是否在窗口期内
            if now - rate_limit.window_start > timedelta(minutes=1):
                rate_limit.count = 1
                rate_limit.window_start = now
                db.commit()
                return True, ""

            # 检查是否超过限制
            if rate_limit.count >= settings.SEND_RATE_LIMIT:
                return False, "发送频率过高，请稍后再试"

            rate_limit.count += 1
            db.commit()
            return True, ""
        finally:
            db.close()

    @staticmethod
    def record_send(user_id: int):
        """记录发送"""
        db = SessionLocal()
        try:
            rate_limit = db.query(SendRateLimit).filter(SendRateLimit.user_id == user_id).first()
            if rate_limit:
                rate_limit.count += 1
                db.commit()
        finally:
            db.close()

    @staticmethod
    def get_inbox(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取收件箱"""
        offset = (page - 1) * page_size

        db = SessionLocal()
        try:
            # 获取总数
            total = db.query(EmailRecipient).filter(
                EmailRecipient.user_id == user_id,
                EmailRecipient.folder == "inbox",
                EmailRecipient.is_deleted == False
            ).count()

            recipients = db.query(EmailRecipient).filter(
                EmailRecipient.user_id == user_id,
                EmailRecipient.folder == "inbox",
                EmailRecipient.is_deleted == False
            ).order_by(EmailRecipient.created_at.desc()).offset(offset).limit(page_size).all()

            result = []
            for r in recipients:
                email = db.query(Email).filter(Email.id == r.email_id).first()
                if email:
                    result.append(MailService._format_email_for_list(email, r))

            return {"total": total, "mails": result}
        finally:
            db.close()

    @staticmethod
    def get_sent(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取发件箱"""
        offset = (page - 1) * page_size

        db = SessionLocal()
        try:
            # 获取总数
            total = db.query(Email).filter(Email.from_user_id == user_id).count()

            emails = db.query(Email).filter(
                Email.from_user_id == user_id
            ).order_by(Email.created_at.desc()).offset(offset).limit(page_size).all()

            result = []
            for e in emails:
                result.append(MailService._format_sent_email(e))

            return {"total": total, "mails": result}
        finally:
            db.close()

    @staticmethod
    def get_drafts(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取草稿箱"""
        offset = (page - 1) * page_size

        db = SessionLocal()
        try:
            total = db.query(Email).filter(
                Email.from_user_id == user_id,
                Email.is_draft == True
            ).count()

            emails = db.query(Email).filter(
                Email.from_user_id == user_id,
                Email.is_draft == True
            ).order_by(Email.updated_at.desc()).offset(offset).limit(page_size).all()

            result = []
            for e in emails:
                result.append(MailService._format_draft_email(e))

            return {"total": total, "mails": result}
        finally:
            db.close()

    @staticmethod
    def _format_email_for_list(email: Email, recipient: EmailRecipient) -> dict:
        """格式化邮件为列表项"""
        db = SessionLocal()
        try:
            from_user = db.query(User).filter(User.id == email.from_user_id).first()
            has_attachment = db.query(EmailAttachment).filter(EmailAttachment.email_id == email.id).count() > 0
            return {
                "id": recipient.id,
                "mail_id": email.mail_uuid,
                "from_addr": email.from_email,
                "from_user": from_user.username if from_user else email.from_email,
                "subject": email.subject,
                "body": email.body[:100] if email.body else "",
                "is_read": recipient.is_read,
                "is_starred": recipient.is_starred,
                "is_phishing": email.is_phishing,
                "has_attachment": has_attachment,
                "created_at": email.created_at.isoformat() if email.created_at else ""
            }
        finally:
            db.close()

    @staticmethod
    def _format_sent_email(email: Email) -> dict:
        """格式化发送邮件为列表项"""
        db = SessionLocal()
        try:
            recipients = db.query(EmailRecipient).filter(EmailRecipient.email_id == email.id).all()
            to_addrs = [db.query(User).filter(User.id == r.user_id).first().email for r in recipients if r.recipient_type == 'to']
            has_attachment = db.query(EmailAttachment).filter(EmailAttachment.email_id == email.id).count() > 0

            return {
                "id": email.id,
                "mail_id": email.mail_uuid,
                "to_addrs": ",".join(to_addrs),
                "subject": email.subject,
                "body": email.body[:100] if email.body else "",
                "is_sent": True,
                "is_recalled": email.is_recalled,
                "has_attachment": has_attachment,
                "created_at": email.created_at.isoformat() if email.created_at else ""
            }
        finally:
            db.close()

    @staticmethod
    def _format_draft_email(email: Email) -> dict:
        """格式化草稿邮件"""
        return {
            "id": email.id,
            "mail_id": email.mail_uuid,
            "subject": email.subject,
            "body": email.body,
            "is_draft": True,
            "created_at": email.updated_at.isoformat() if email.updated_at else email.created_at.isoformat() if email.created_at else ""
        }

    @staticmethod
    def get_mail_detail(mail_id: int, user_id: int) -> Optional[dict]:
        """获取邮件详情"""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == mail_id).first()
            if not email:
                return None

            # 检查权限
            is_sender = email.from_user_id == user_id

            recipient = db.query(EmailRecipient).filter(
                EmailRecipient.email_id == email.id,
                EmailRecipient.user_id == user_id
            ).first()

            if not is_sender and not recipient:
                return None

            # 标记为已读
            if recipient and not recipient.is_read:
                recipient.is_read = True
                recipient.read_at = datetime.utcnow()
                db.commit()

            # 获取附件
            attachments = db.query(EmailAttachment).filter(EmailAttachment.email_id == email.id).all()

            # 获取收件人
            recipients = db.query(EmailRecipient).filter(EmailRecipient.email_id == email.id).all()

            return {
                "id": email.id,
                "mail_id": email.mail_uuid,
                "from_addr": email.from_email,
                "to_addrs": ",".join([db.query(User).filter(User.id == r.user_id).first().email for r in recipients if r.recipient_type == 'to']),
                "cc_addrs": ",".join([db.query(User).filter(User.id == r.user_id).first().email for r in recipients if r.recipient_type == 'cc']),
                "subject": email.subject,
                "body": email.body,
                "is_read": recipient.is_read if recipient else True,
                "is_starred": recipient.is_starred if recipient else False,
                "is_recalled": email.is_recalled,
                "is_draft": email.is_draft,
                "is_phishing": email.is_phishing,
                "keywords": (email.keywords or "").split(","),
                "created_at": email.created_at.isoformat() if email.created_at else "",
                "attachments": [
                    {
                        "id": a.id,
                        "filename": a.filename,
                        "content_type": a.content_type,
                        "size": a.size,
                        "file_id": a.file_id
                    }
                    for a in attachments
                ]
            }
        finally:
            db.close()

    @staticmethod
    def mark_as_read(mail_id: int, user_id: int) -> bool:
        """标记为已读"""
        db = SessionLocal()
        try:
            recipient = db.query(EmailRecipient).filter(
                EmailRecipient.email_id == mail_id,
                EmailRecipient.user_id == user_id
            ).first()

            if recipient:
                recipient.is_read = True
                recipient.read_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def toggle_star(mail_id: int, user_id: int) -> Optional[bool]:
        """切换星标"""
        db = SessionLocal()
        try:
            recipient = db.query(EmailRecipient).filter(
                EmailRecipient.email_id == mail_id,
                EmailRecipient.user_id == user_id
            ).first()

            if recipient:
                recipient.is_starred = not recipient.is_starred
                db.commit()
                return recipient.is_starred
            return None
        finally:
            db.close()

    @staticmethod
    def recall_mail(mail_id: int, user_id: int) -> dict:
        """撤回邮件"""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == mail_id).first()

            if not email:
                return {"success": False, "message": "邮件不存在"}

            # 检查是否是发件人
            if email.from_user_id != user_id:
                return {"success": False, "message": "只有发件人才能撤回邮件"}

            # 检查是否超过24小时
            if datetime.utcnow() - email.created_at > timedelta(hours=24):
                return {"success": False, "message": "邮件已超过24小时，无法撤回"}

            # 标记撤回
            email.is_recalled = True
            email.recalled_at = datetime.utcnow()
            db.commit()

            return {"success": True, "message": "邮件已撤回"}
        finally:
            db.close()

    @staticmethod
    def quick_reply(mail_id: int, user_id: int, body: str) -> dict:
        """快捷回复"""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == mail_id).first()
            if not email:
                return {"success": False, "message": "邮件不存在"}

            sender = db.query(User).filter(User.id == user_id).first()
            if not sender:
                return {"success": False, "message": "用户不存在"}

            # 发送回复
            reply_uuid = str(uuid.uuid4())
            reply_email = Email(
                mail_uuid=reply_uuid,
                subject=f"Re: {email.subject}",
                body=body,
                from_user_id=sender.id,
                from_email=sender.email,
                domain_id=sender.domain_id
            )
            db.add(reply_email)
            db.commit()
            db.refresh(reply_email)

            # 创建收件人
            recipient_user = db.query(User).filter(User.email == email.from_email).first()
            if recipient_user:
                rec = EmailRecipient(
                    email_id=reply_email.id,
                    user_id=recipient_user.id,
                    recipient_type='to'
                )
                db.add(rec)
                db.commit()

            return {"success": True, "message": "回复已发送", "data": {"mail_id": reply_uuid}}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def search_mail(user_id: int, keyword: str, folder: str = "inbox", page: int = 1, page_size: int = 20) -> dict:
        """搜索邮件"""
        offset = (page - 1) * page_size
        keyword_lower = keyword.lower()

        db = SessionLocal()
        try:
            if folder == "sent":
                # 搜索发件箱
                query = db.query(Email).filter(
                    Email.from_user_id == user_id,
                    Email.is_draft == False,
                    (Email.subject.ilike(f"%{keyword_lower}%")) | (Email.body.ilike(f"%{keyword_lower}%"))
                )
                total = query.count()
                emails = query.order_by(Email.created_at.desc()).offset(offset).limit(page_size).all()

                result = [MailService._format_sent_email(e) for e in emails]
            else:
                # 搜索收件箱
                recipients = db.query(EmailRecipient).filter(
                    EmailRecipient.user_id == user_id,
                    EmailRecipient.folder == "inbox",
                    EmailRecipient.is_deleted == False
                ).all()

                results = []
                for r in recipients:
                    email = db.query(Email).filter(Email.id == r.email_id).first()
                    if email and not email.is_draft and (keyword_lower in email.subject.lower() or keyword_lower in email.body.lower()):
                        results.append(MailService._format_email_for_list(email, r))

                total = len(results)
                result = results[offset:offset + page_size]

            return {"total": total, "mails": result}
        finally:
            db.close()
    @staticmethod
    def mark_as_todo(mail_id: int, user_id: int) -> bool:
        """标记为待办"""
        db = SessionLocal()
        try:
            recipient = db.query(EmailRecipient).filter(
                EmailRecipient.email_id == mail_id,
                EmailRecipient.user_id == user_id
            ).first()
            
            if not recipient:
                # 尝试从发件箱中查找
                email = db.query(Email).filter(
                    Email.id == mail_id,
                    Email.from_user_id == user_id
                ).first()
                if email:
                    # 对于自己发送的邮件，也支持标记为待办
                    email.is_starred = not email.is_starred
                    db.commit()
                    return email.is_starred
                return False
            
            # 切换待办状态
            recipient.is_starred = not recipient.is_starred
            db.commit()
            return recipient.is_starred
        finally:
            db.close()

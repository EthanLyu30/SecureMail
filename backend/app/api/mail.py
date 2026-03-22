"""
邮件相关API - 支持跨域邮件
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.services.mail_service import MailService
from app.services.relay_service import MailRelayService, MailRelaySync
from app.api.deps import get_current_user


router = APIRouter(prefix="/mail", tags=["邮件"])


class SendEmailRequest(BaseModel):
    """发送邮件请求"""
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    subject: str
    body: str
    is_html: bool = False
    is_draft: bool = False
    attachments: Optional[List[dict]] = []


class RelayReceiveRequest(BaseModel):
    """中继接收请求"""
    from_email: str
    to_addrs: List[str]
    cc_addrs: Optional[List[str]] = []
    bcc_addrs: Optional[List[str]] = []
    subject: str
    body: str
    is_html: bool = False


class MailResponse(BaseModel):
    """邮件响应"""
    id: int
    from_addr: str = ""
    to_addrs: str = ""
    cc_addrs: Optional[str] = ""
    bcc_addrs: Optional[str] = ""
    subject: str
    body: str
    is_read: bool = False
    is_starred: bool = False
    is_draft: bool = False
    is_sent: bool = False
    created_at: str
    attachments: str = "[]"


class MailListResponse(BaseModel):
    """邮件列表响应"""
    total: int
    mails: List[MailResponse]


class RecallRequest(BaseModel):
    """邮件撤回请求"""
    mail_id: int


class QuickReplyRequest(BaseModel):
    """快捷回复请求"""
    mail_id: int
    body: str


@router.post("/send", response_model=dict)
def send_email(
    req: SendEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """发送邮件（支持跨域）"""
    # 检查是否有跨域收件人
    current_domain = current_user.get("domain", "")
    other_domains = []
    
    for recipient in req.to:
        if "@" in recipient:
            _, domain = recipient.split("@", 1)
            if domain != current_domain:
                other_domains.append(recipient)
    
    # 先发送到本地域用户
    local_recipients = [r for r in req.to if r not in other_domains]
    
    result = None
    if local_recipients:
        result = MailService.send_email(
            user_id=current_user["user_id"],
            to_addrs=local_recipients,
            cc_addrs=req.cc or [],
            bcc_addrs=req.bcc or [],
            subject=req.subject,
            body=req.body,
            is_html=req.is_html,
            is_draft=req.is_draft,
            attachments=req.attachments or []
        )
    
    # 如果有跨域收件人，尝试中继
    relayed = False
    if other_domains:
        mail_data = {
            "from_email": current_user.get("email"),
            "to_addrs": other_domains,
            "cc_addrs": req.cc or [],
            "bcc_addrs": req.bcc or [],
            "subject": req.subject,
            "body": req.body,
            "is_html": req.is_html
        }
        
        # 尝试中继到第一个跨域目标
        relay_result = MailRelaySync.forward_to_domain_sync(
            other_domains[0], 
            mail_data
        )
        relayed = relay_result.get("relayed", False)
        
        # 如果本地发送也成功，则整体成功
        if result and result.get("success"):
            return {
                "success": True, 
                "message": f"邮件已发送，其中{len(other_domains)}封已中继到其他域名",
                "data": result.get("data")
            }
    
    if result and result.get("success"):
        return result
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "发送失败") if result else "发送失败"
    )


@router.post("/relay/receive", response_model=dict)
def relay_receive_mail(req: RelayReceiveRequest):
    """接收跨域中继邮件（内部接口）"""
    result = MailRelayService.receive_relay_mail({
        "from_email": req.from_email,
        "to_addrs": req.to_addrs,
        "cc_addrs": req.cc_addrs or [],
        "bcc_addrs": req.bcc_addrs or [],
        "subject": req.subject,
        "body": req.body,
        "is_html": req.is_html
    })
    
    if result.get("success"):
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message")
    )


@router.get("/inbox", response_model=MailListResponse)
def get_inbox(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """获取收件箱"""
    result = MailService.get_inbox(
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size
    )
    return MailListResponse(**result)


@router.get("/sent", response_model=MailListResponse)
def get_sent(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """获取发件箱"""
    result = MailService.get_sent(
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size
    )
    return MailListResponse(**result)


@router.get("/drafts", response_model=MailListResponse)
def get_drafts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """获取草稿箱"""
    result = MailService.get_drafts(
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size
    )
    return MailListResponse(**result)


@router.get("/detail/{mail_id}", response_model=MailResponse)
def get_mail_detail(
    mail_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取邮件详情"""
    mail = MailService.get_mail_detail(mail_id, current_user["user_id"])
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    return MailResponse(**mail)


@router.post("/read/{mail_id}", response_model=dict)
def mark_as_read(
    mail_id: int,
    current_user: dict = Depends(get_current_user)
):
    """标记为已读"""
    result = MailService.mark_as_read(mail_id, current_user["user_id"])
    if result:
        return {"success": True}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="邮件不存在"
    )


@router.post("/star/{mail_id}", response_model=dict)
def toggle_star(
    mail_id: int,
    current_user: dict = Depends(get_current_user)
):
    """标记/取消星标"""
    result = MailService.toggle_star(mail_id, current_user["user_id"])
    if result is not None:
        return {"success": True, "is_starred": result}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="邮件不存在"
    )


@router.post("/recall", response_model=dict)
def recall_mail(
    req: RecallRequest,
    current_user: dict = Depends(get_current_user)
):
    """撤回邮件"""
    result = MailService.recall_mail(req.mail_id, current_user["user_id"])
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "撤回失败")
    )


@router.post("/quick-reply", response_model=dict)
def quick_reply(
    req: QuickReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """快捷回复"""
    result = MailService.quick_reply(
        req.mail_id,
        current_user["user_id"],
        req.body
    )
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "回复失败")
    )


class ReplyRequest(BaseModel):
    """直接回复请求"""
    body: str


@router.post("/{mail_id}/reply", response_model=dict)
def reply_to_mail(
    mail_id: int,
    request: ReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """快捷回复邮件"""
    result = MailService.quick_reply(mail_id, current_user["user_id"], request.body)
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "回复失败")
    )


@router.post("/{mail_id}/todo", response_model=dict)
def mark_as_todo(
    mail_id: int,
    current_user: dict = Depends(get_current_user)
):
    """添加到待办"""
    result = MailService.mark_as_todo(mail_id, current_user['user_id'])
    if result:
        return {"success": True, "is_todo": result}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="邮件不存在"
    )


@router.get("/search", response_model=MailListResponse)
def search_mail(
    keyword: str = Query(...),
    folder: str = Query("inbox"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """搜索邮件"""
    result = MailService.search_mail(
        user_id=current_user["user_id"],
        keyword=keyword,
        folder=folder,
        page=page,
        page_size=page_size
    )
    return MailListResponse(**result)


@router.get("/keywords/{mail_id}")
def get_mail_keywords(
    mail_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取邮件关键词"""
    mail = MailService.get_mail_detail(mail_id, current_user["user_id"])
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    return {"keywords": mail.get("keywords", [])}


@router.post("/attachment/download/{file_id}")
def download_attachment(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """下载附件"""
    from app.core.config import settings
    import os
    import base64
    
    file_path = os.path.join(settings.ATTACHMENT_DIR, file_id)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    filename = os.path.basename(file_id)
    # 尝试从原始名称获取
    db = SessionLocal()
    try:
        from app.models import EmailAttachment
        att = db.query(EmailAttachment).filter(EmailAttachment.file_id == file_id).first()
        if att:
            filename = att.filename
    finally:
        db.close()
    
    return {
        "filename": filename,
        "data": data
    }


# 导入SessionLocal用于附件下载
from app.models import SessionLocal
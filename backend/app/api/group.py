"""
群组相关API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.services.group_service import GroupService
from app.api.deps import get_current_user


router = APIRouter(prefix="/group", tags=["群组"])


class CreateGroupRequest(BaseModel):
    """创建群组请求"""
    name: str
    description: str = ""
    members: List[str] = []


class UpdateGroupRequest(BaseModel):
    """更新群组请求"""
    name: str = ""
    description: str = ""
    members: List[str] = []


class GroupResponse(BaseModel):
    """群组响应"""
    id: int
    name: str
    description: str
    owner_id: int
    members: str
    created_at: str


class GroupListResponse(BaseModel):
    """群组列表响应"""
    total: int
    groups: List[GroupResponse]


@router.post("/", response_model=dict)
def create_group(
    req: CreateGroupRequest,
    current_user: dict = Depends(get_current_user)
):
    """创建群组"""
    result = GroupService.create_group(
        owner_id=current_user["user_id"],
        name=req.name,
        description=req.description,
        members=req.members
    )
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "创建失败")
    )


@router.get("/", response_model=GroupListResponse)
def get_groups(
    current_user: dict = Depends(get_current_user)
):
    """获取群组列表"""
    result = GroupService.get_groups(current_user["user_id"])
    return GroupListResponse(**result)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取群组详情"""
    group = GroupService.get_group(group_id, current_user["user_id"])
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群组不存在"
        )
    return GroupResponse(**group)


@router.put("/{group_id}", response_model=dict)
def update_group(
    group_id: int,
    req: UpdateGroupRequest,
    current_user: dict = Depends(get_current_user)
):
    """更新群组"""
    result = GroupService.update_group(
        group_id=group_id,
        owner_id=current_user["user_id"],
        name=req.name,
        description=req.description,
        members=req.members
    )
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "更新失败")
    )


@router.delete("/{group_id}", response_model=dict)
def delete_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除群组"""
    result = GroupService.delete_group(group_id, current_user["user_id"])
    if result["success"]:
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "删除失败")
    )
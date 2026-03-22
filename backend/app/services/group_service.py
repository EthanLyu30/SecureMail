"""
群组服务 - 同步版本
"""
from typing import List, Tuple, Optional

from app.models import Group, GroupMember, User, SessionLocal


class GroupService:
    """群组服务"""

    @staticmethod
    def create_group(name: str, owner_id: int, domain_id: int) -> Tuple[bool, str, Optional[int]]:
        """创建群组"""
        db = SessionLocal()
        try:
            group = Group(
                name=name,
                owner_id=owner_id,
                domain_id=domain_id
            )
            db.add(group)
            db.commit()
            db.refresh(group)

            # 创建者自动成为成员
            member = GroupMember(
                group_id=group.id,
                user_id=owner_id,
                role="owner"
            )
            db.add(member)
            db.commit()

            return True, "群组已创建", group.id
        finally:
            db.close()

    @staticmethod
    def get_user_groups(user_id: int) -> List[dict]:
        """获取用户群组"""
        db = SessionLocal()
        try:
            memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()

            groups = []
            for m in memberships:
                group = db.query(Group).filter(Group.id == m.group_id).first()
                if group:
                    # 获取所有成员
                    members_data = []
                    members = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
                    for member in members:
                        user = db.query(User).filter(User.id == member.user_id).first()
                        if user:
                            members_data.append({
                                "id": user.id,
                                "username": user.username,
                                "email": user.email
                            })

                    groups.append({
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "role": m.role,
                        "members": members_data
                    })

            return groups
        finally:
            db.close()

    @staticmethod
    def add_member(group_id: int, owner_id: int, member_username: str, domain_id: int) -> Tuple[bool, str]:
        """添加群组成员"""
        db = SessionLocal()
        try:
            # 检查群组是否存在
            group = db.query(Group).filter(Group.id == group_id).first()
            if not group:
                return False, "群组不存在"

            # 检查权限
            if group.owner_id != owner_id:
                return False, "只有群主可以添加成员"

            # 查找用户
            user = db.query(User).filter(
                User.username == member_username,
                User.domain_id == domain_id
            ).first()

            if not user:
                return False, "用户不存在"

            # 检查是否已是成员
            existing = db.query(GroupMember).filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user.id
            ).first()

            if existing:
                return False, "用户已在群组中"

            # 添加成员
            member = GroupMember(
                group_id=group_id,
                user_id=user.id,
                role="member"
            )
            db.add(member)
            db.commit()

            return True, "成员已添加"
        finally:
            db.close()

    @staticmethod
    def remove_member(group_id: int, owner_id: int, member_id: int) -> Tuple[bool, str]:
        """移除群组成员"""
        db = SessionLocal()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if not group:
                return False, "群组不存在"

            if group.owner_id != owner_id:
                return False, "只有群主可以移除成员"

            member = db.query(GroupMember).filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == member_id
            ).first()

            if not member:
                return False, "成员不存在"

            if member.role == "owner":
                return False, "不能移除群主"

            db.delete(member)
            db.commit()
            return True, "成员已移除"
        finally:
            db.close()
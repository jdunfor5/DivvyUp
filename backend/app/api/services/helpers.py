from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
#from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.group import Group, GroupMember, GroupMemberRole

async def is_user_a_group_member(db: AsyncSession, user_uuid: UUID, group_uuid: UUID):
    statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
    result = await db.execute(statement)
    group_member = result.scalar_one_or_none()

    return True if group_member else False

async def is_user_a_group_admin(db: AsyncSession, user_uuid: UUID, group_uuid: UUID):
    statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid, GroupMember.role == GroupMemberRole.admin)
    result = await db.execute(statement)
    group_admin = result.scalar_one_or_none()

    return True if group_admin else False

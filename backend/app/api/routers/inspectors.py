from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.user import UserRead
from ...models.group import GroupRead, GroupMemberRead
from ...models.notification import Notification, NotificationRead
from ..services import inspectors as service

router = APIRouter(
    tags=["inspector"],
    prefix="/inspector"
)

@router.get("/users", response_model=list[UserRead])
async def read_all_users(db: AsyncSession = Depends(get_session)):
    return await service.read_all_users(db)

@router.get("/groups", response_model=list[GroupRead])
async def read_all_groups(db: AsyncSession = Depends(get_session)):
    return await service.read_all_groups(db)

@router.get("/groups/members", response_model=list[GroupMemberRead])
async def read_all_group_members(db: AsyncSession = Depends(get_session)):
    return await service.read_all_group_members(db)

# NOTE: This has yet to be functional because NotificationCreate has yet to be implemented.
# @router.post("/notifications")
# async def create_notification(request: Notification, db: AsyncSession = Depends(get_session)):
#     return await service.create_notification(db, request)

@router.get("/notifications", response_model=list[NotificationRead])
async def read_all_notifications(db: AsyncSession = Depends(get_session)):
    return await service.read_all_notifications(db)

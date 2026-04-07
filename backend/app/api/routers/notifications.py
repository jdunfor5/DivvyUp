from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.notification import NotificationRead
from ..services import notifications as service

router = APIRouter(
    tags=["notifications"],
    prefix="/notifications"
)

@router.get("/", response_model=list[NotificationRead])
async def read_current_user_notifications(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_current_user_notifications(db, current_user)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_notifications(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_current_user_notifications(db, current_user)

@router.get("/{notification_uuid}", response_model=NotificationRead)
async def read_current_user_notification(notification_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_current_user_notification(db, current_user, notification_uuid)

@router.delete("/{notification_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_notification(notification_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_current_user_notification(db, current_user, notification_uuid)
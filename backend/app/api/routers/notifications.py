from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.notification import NotificationRead
from ..services import notifications as service

router = APIRouter(
    tags=["notifications"],
    prefix="/users/{user_uuid}/notifications"
)

# GET: Read notification endpoint
@router.get("/{notification_uuid}", response_model=NotificationRead)
async def read(user_uuid: UUID, notification_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read(db=db, user_uuid=user_uuid, notification_uuid=notification_uuid)

# GET: Read all notification endpoint
@router.get("/", response_model=list[NotificationRead])
async def read_all(user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read_all(db=db, user_uuid=user_uuid)
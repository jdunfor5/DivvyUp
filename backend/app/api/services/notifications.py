from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.notification import Notification
from ...models.user import UserRead


async def read_current_user_notifications(db: AsyncSession, current_user: UserRead):
    try:
        statement = select(Notification).where(Notification.user_id == current_user.id)
        result = await db.execute(statement)
        notifications = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return notifications


async def read_current_user_notification(db: AsyncSession, current_user: UserRead, notification_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.id == notification_uuid, Notification.user_id == current_user.id)
        result = await db.execute(statement)
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{notification_uuid} is an invalid notification identifier.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return notification


async def delete_current_user_notifications(db: AsyncSession, current_user: UserRead):
    try:
        statement = delete(Notification).where(Notification.user_id == current_user.id)
        await db.execute(statement)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None


async def delete_current_user_notification(db: AsyncSession, current_user: UserRead, notification_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.id == notification_uuid, Notification.user_id == current_user.id)
        result = await db.execute(statement)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{notification_uuid} is an invalid notification identifier.")

        await db.execute(delete(Notification).where(Notification.id == notification_uuid, Notification.user_id == current_user.id))
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None
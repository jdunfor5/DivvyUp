from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User
from ...models.group import Group, GroupMember
from ...models.notification import Notification
from ...dependencies.logging import get_logger

logger = get_logger(__name__)

async def read_all_users(db: AsyncSession):
    try:
        statement = select(User)
        result = await db.execute(statement)
        users = result.scalars().all()

    except SQLAlchemyError as e:
        logger.warning("Database error reading all users: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return users

async def read_all_groups(db: AsyncSession):
    try:
        statement = select(Group)
        result = await db.execute(statement)
        groups = result.scalars().all()

    except SQLAlchemyError as e:
        logger.warning("Database error reading all groups: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return groups

async def read_all_group_members(db: AsyncSession):
    try:
        statement = select(GroupMember)
        result = await db.execute(statement)
        group_members = result.scalars().all()

    except SQLAlchemyError as e:
        logger.warning("Database error reading all group members: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group_members

async def create_notification(db: AsyncSession, request: Notification):
    new_notification = Notification(
        user_id         = request.user_id,
        type            = request.type,
        title           = request.title,
        body            = request.body,
        related_id      = request.related_id
    )

    try:
        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)
    except SQLAlchemyError as e:
        logger.warning("Database error creating notification: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return new_notification

async def read_all_notifications(db: AsyncSession):
    try:
        statement = select(Notification)
        result = await db.execute(statement)
        notifications = result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("Database error reading all notifications: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return notifications

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User
from ...models.group import Group, GroupMember
from ...models.notification import Notification

async def read_all_users(db: AsyncSession):
    try:
        statement = select(User)
        result = await db.execute(statement)
        users = result.scalars().all()
        
        if not users:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users exist in the database.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return users

async def read_all_groups(db: AsyncSession):
    try:
        statement = select(Group)
        result = await db.execute(statement)
        groups = result.scalars().all()
        
        if not groups:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No groups exist in the database.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return groups

async def read_all_group_members(db: AsyncSession):
    try:
        statement = select(GroupMember)
        result = await db.execute(statement)
        group_members = result.scalars().all()
        
        if not group_members:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No group members exist in the database. Thus, no groups should exist in the database.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
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
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {f"{new_notification.id} has been added into the \"notifications\" table."}

async def read_all_notifications(db: AsyncSession):
    try:
        statement = select(Notification)
        result = await db.execute(statement)
        notifications = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return notifications

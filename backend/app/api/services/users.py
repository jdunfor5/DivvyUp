from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User, UserCreate, UserRead, UserUpdate
from ...models.group import Group, GroupMember, GroupMemberRole
from ...dependencies.security import hash_password, sanitize_emoji
from ...dependencies.logging import get_logger

logger = get_logger(__name__)

async def create_user(db: AsyncSession, request: UserCreate):
    new_user = User(
        email           = request.email,
        password_hash   = hash_password(request.password),
        avatar_emoji    = sanitize_emoji(request.avatar_emoji),
        display_name    = request.display_name,
        phone           = request.phone,
        base_currency   = request.base_currency
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except SQLAlchemyError as e:
        logger.warning("Database error creating user: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return new_user

async def read_user(db: AsyncSession, current_user: UserRead, user_uuid: UUID):
    if current_user.id != user_uuid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own profile.")

    try:
        statement = select(User).where(User.id == user_uuid)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    except SQLAlchemyError as e:
        logger.warning("Database error reading user %s: %s", user_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return user

async def update_current_user(db: AsyncSession, current_user: UserRead, request: UserUpdate):
    try:
        statement = select(User).where(User.id == current_user.id)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        update_user = request.model_dump(exclude_unset=True)

        for field, value in update_user.items():
            if field == "avatar_emoji":
                value = sanitize_emoji(value)
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        logger.warning("Database error updating user %s: %s", current_user.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return user

async def delete_current_user(db: AsyncSession, current_user: UserRead):
    try:
        admin_check = await db.execute(
            select(GroupMember).where(
                GroupMember.user_id == current_user.id,
                GroupMember.role == GroupMemberRole.admin
            )
        )
        admin_memberships = admin_check.scalars().all()
        if admin_memberships:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are the admin of one or more groups. Transfer ownership or delete those groups before deleting your account."
            )

        created_check = await db.execute(
            select(Group).where(Group.created_by == current_user.id)
        )
        created_groups = created_check.scalars().all()
        for group in created_groups:
            admin_result = await db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == group.id,
                    GroupMember.role == GroupMemberRole.admin
                )
            )
            admin = admin_result.scalar_one_or_none()
            if admin:
                group.created_by = admin.user_id

        statement = select(User).where(User.id == current_user.id)
        user = await db.scalar(statement)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        await db.delete(user)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error deleting user %s: %s", current_user.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None

async def search(db: AsyncSession, current_user: UserRead, email_query: str):
    try:
        statement = (
            select(User)
            .where(User.email.ilike(f"%{email_query}%"), User.id != current_user.id)
            .limit(10)
        )
        result = await db.execute(statement)
        users = result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("Database error searching users: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return users

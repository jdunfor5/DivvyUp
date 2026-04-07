from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User, UserCreate, UserRead, UserUpdate
from ...dependencies.security import hash_password

async def create_user(db: AsyncSession, request: UserCreate):
    new_user = User(
        email           = request.email,
        password_hash   = hash_password(request.password),
        display_name    = request.display_name,
        phone           = request.phone,
        base_currency   = request.base_currency
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {"message": f"{new_user.id} has been added into the \"users\" table."}

async def read_user(db: AsyncSession, user_uuid: UUID):
    try:
        statement = select(User).where(User.id == user_uuid)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the \"users\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return user

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
# backend/app/api/routers/auth.py includes an endpoint: /auth/token
#
# This function throws if one attempts to update all fields due to some kind of database character limit.
async def update_current_user(db: AsyncSession, current_user: UserRead, request: UserUpdate):
    try:
        statement = select(User).where(User.id == current_user.id)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{current_user.id} is an invalid user identifier. That is, entity does not exist in the \"users\" table.")

        update_user = request.model_dump(exclude_unset=True)

        for field, value in update_user.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return user

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
# backend/app/api/routers/auth.py includes an endpoint: /auth/token
#
# Any references to current_user (that is, as a foreign key) will not delete the user.
# - A user that is a part of a group will need to leave before trying to delete their account.
# - A user that has notifications will need to delete them before trying to delete their account.
#
# Jacob suggested writing to a flag to as opposed to outright deleting the current user.
async def delete_current_user(db: AsyncSession, current_user: UserRead):
    try:
        statement = select(User).where(User.id == current_user.id)
        user = await db.scalar(statement)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{current_user.id} is an invalid user identifier. That is, entity does not exist in the \"users\" table.")

        await db.delete(user)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None
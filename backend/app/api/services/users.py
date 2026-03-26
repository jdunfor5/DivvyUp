from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User, UserCreate, UserUpdate

# TODO:
# Password is currently plaintext at this point and requries hashing.
# 
# POST: Create user endpoint
async def create(db: AsyncSession, request: UserCreate):
    new_user = User(
        email           = request.email,
        password_hash   = request.password,
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

    return {"User created successfully"}
    
# TODO:
# Allow any user to read other user details?
# Password is not returned thanks to UserRead scheme.
# 
# GET: Read user details endpoint
async def read(db: AsyncSession, user_uuid: UUID):
    try:
        statement = select(User).where(User.id == user_uuid)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return user

# TODO:
# Security-wise, check the logged in user and determine if they match the requested user.
# Currently, I am not aware of a system in place that reads the logged in user.
# We will need to create that.
#
# PATCH: Update user endpoint
async def update(db: AsyncSession, user_uuid: UUID, request: UserUpdate):
    try:
        statement = select(User).where(User.id == user_uuid)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
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
# Security-wise, only the logged in user should delete their own account.
#
# DELETE: Delete user endpoint
async def delete(db: AsyncSession, user_uuid: UUID):
    try:
        statement = select(User).where(User.id == user_uuid)
        user = await db.scalar(statement=statement)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        await db.delete(user)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"User deleted successfully"}
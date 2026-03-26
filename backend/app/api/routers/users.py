from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.user import UserCreate, UserRead, UserUpdate
from ..services import users as service

router = APIRouter(
    tags=["users"],
    prefix="/users"
)

# POST: Create user endpoint
@router.post("/")
async def create(request: UserCreate, db: AsyncSession = Depends(get_session)): 
    return await service.create(db=db, request=request)

# GET: Read user details endpoint
@router.get("/{user_uuid}", response_model=UserRead)
async def read(user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read(db=db, user_uuid=user_uuid)

# PATCH: Update user endpoint
@router.patch("/{user_uuid}", response_model=UserUpdate)
async def update(user_uuid: UUID, request: UserUpdate, db: AsyncSession = Depends(get_session)):
    return await service.update(db=db, user_uuid=user_uuid, request=request)

# DELETE: Delete user endpoint
@router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.delete(db=db, user_uuid=user_uuid)
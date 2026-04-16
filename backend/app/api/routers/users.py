from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserCreate, UserRead, UserUpdate
from ..services import users as service

router = APIRouter(
    tags=["users"],
    prefix="/users"
)

@router.post("/", response_model=UserRead)
async def create_user(request: UserCreate, db: AsyncSession = Depends(get_session)):
    return await service.create_user(db, request)

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)):
    return current_user

@router.get("/search", response_model=list[UserRead])
async def search_users(email: str = Query(..., min_length=1), current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.search(db, current_user, email)

@router.get("/{user_uuid}", response_model=UserRead)
async def read_user(user_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_user(db, current_user, user_uuid)

@router.patch("/me", response_model=UserRead)
async def update_current_user(request: UserUpdate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.update_current_user(db, current_user, request)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_current_user(db, current_user)

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.friendship import FriendRead
from ..services import friendships as service

router = APIRouter(
    tags=["friends"],
    prefix="/friends"
)

@router.post("/{friend_uuid}", status_code=status.HTTP_201_CREATED)
async def add_friend(friend_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.add_friend(db, current_user, friend_uuid)

@router.get("/", response_model=list[FriendRead])
async def list_friends(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.list_friends(db, current_user)

@router.get("/{friend_uuid}", response_model=FriendRead)
async def get_friend(friend_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.get_friend(db, current_user, friend_uuid)

@router.delete("/{friend_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(friend_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.remove_friend(db, current_user, friend_uuid)

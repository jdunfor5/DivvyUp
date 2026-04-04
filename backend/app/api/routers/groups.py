from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.group import GroupCreate, GroupRead, GroupUpdate, GroupMemberRead
from ..services import groups as service

router = APIRouter(
    tags=["groups"],
    prefix="/groups"
)

@router.post("/")
async def create_group(request: GroupCreate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create_group(db, current_user, request)

@router.get("/", response_model=list[GroupRead])
async def read_current_user_groups(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_current_user_groups(db, current_user)

@router.post("/{group_uuid}")
async def create_group_member(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create_group_member(db, current_user, group_uuid)

@router.get("/{group_uuid}", response_model=GroupRead)
async def read_group(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_group(db, group_uuid)

@router.patch("/{group_uuid}", response_model=GroupUpdate)
async def update_group(request: GroupUpdate, group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.update_group(db, group_uuid, request)

@router.delete("/{group_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_group(db, current_user, group_uuid)

@router.delete("/{group_uuid}/members", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_group_member(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_current_group_member(db, current_user, group_uuid)

@router.get("/{group_uuid}/members/{user_uuid}", response_model=GroupMemberRead)
async def read_group_member(user_uuid: UUID, group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_group_member(db, current_user, group_uuid, user_uuid)

@router.delete("/{group_uuid}/members/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_member(user_uuid: UUID, group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_group_member(db, current_user, group_uuid, user_uuid)

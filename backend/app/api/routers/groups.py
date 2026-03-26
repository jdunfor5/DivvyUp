from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.group import GroupCreate, GroupRead, GroupUpdate, GroupMemberRead
from ..services import groups as service

router = APIRouter(
    tags=["groups"],
    prefix="/groups"
)

# POST: Create group endpoint
@router.post("/")
async def create(request: GroupCreate, db: AsyncSession = Depends(get_session)):
    return await service.create(db=db, request=request)

# POST: Create group member endpoint
@router.post("/{group_uuid}/join")
async def create_member(group_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.create_member(db=db, group_uuid=group_uuid)

# GET: Read group details endpoint
@router.get("/{group_uuid}", response_model=GroupRead)
async def read(group_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read(db=db, group_uuid=group_uuid)

# GET: Read group member endpoint
@router.get("/{group_uuid}/{user_uuid}", response_model=GroupMemberRead)
async def read_member(group_uuid: UUID, user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read_member(db=db, group_uuid=group_uuid, user_uuid=user_uuid)

# PATCH: Update group endpoint
@router.patch("/{group_uuid}", response_model=GroupUpdate)
async def update(group_uuid: UUID, request: GroupUpdate, db: AsyncSession = Depends(get_session)):
    return await service.update(db=db, group_uuid=group_uuid, request=request)

# DELETE: Delete group endpoint
@router.delete("/{group_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(group_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.delete(db=db, group_uuid=group_uuid)

# DELETE: Delete group member endpoint
@router.delete("/{group_uuid}/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(group_uuid: UUID, user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.delete_member(db=db, group_uuid=group_uuid, user_uuid=user_uuid)
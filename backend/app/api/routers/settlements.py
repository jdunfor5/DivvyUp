from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.settlement import SettlementCreate, SettlementRead
from ..services import settlements as service

router = APIRouter(
    tags=["settlements"],
    prefix="/groups/{group_uuid}/settlements"
)

@router.post("/{payee_uuid}", response_model=SettlementRead)
async def create(group_uuid: UUID, payee_uuid: UUID, request: SettlementCreate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create(db, current_user, group_uuid, payee_uuid, request)

@router.get("/", response_model=list[SettlementRead])
async def read_all(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_all(db, current_user, group_uuid)

@router.get("/{settlement_uuid}", response_model=SettlementRead)
async def read(group_uuid: UUID, settlement_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read(db, current_user, group_uuid, settlement_uuid)

@router.patch("/{settlement_uuid}/confirm", response_model=SettlementRead)
async def confirm(group_uuid: UUID, settlement_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.confirm(db, current_user, group_uuid, settlement_uuid)

@router.patch("/{settlement_uuid}/cancel", response_model=SettlementRead)
async def cancel(group_uuid: UUID, settlement_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.cancel(db, current_user, group_uuid, settlement_uuid)
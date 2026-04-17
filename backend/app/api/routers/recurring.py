from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...dependencies.config import settings
from ...models.user import UserRead
from ...models.recurring import RecurringExpenseCreate, RecurringExpenseRead, RecurringExpenseUpdate, RecurringExpenseSplitRead
from ..services import recurring as service

router = APIRouter(
    tags=["recurring expenses"],
    prefix="/groups/{group_uuid}/recurring"
)

cron_router = APIRouter(
    tags=["cron"],
    prefix="/recurring"
)

@router.post("/", response_model=RecurringExpenseRead)
async def create(group_uuid: UUID, request: RecurringExpenseCreate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create(db, current_user, group_uuid, request)

@router.get("/", response_model=list[RecurringExpenseRead])
async def read_all(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_all(db, current_user, group_uuid)

@router.get("/{recurring_uuid}", response_model=RecurringExpenseRead)
async def read(group_uuid: UUID, recurring_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read(db, current_user, group_uuid, recurring_uuid)


@router.get("/{recurring_uuid}/splits", response_model=list[RecurringExpenseSplitRead])
async def read_splits(group_uuid: UUID, recurring_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_splits(db, current_user, group_uuid, recurring_uuid)

@router.patch("/{recurring_uuid}", response_model=RecurringExpenseRead)
async def update(group_uuid: UUID, recurring_uuid: UUID, request: RecurringExpenseUpdate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.update(db, current_user, group_uuid, recurring_uuid, request)

@router.delete("/{recurring_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate(group_uuid: UUID, recurring_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.deactivate(db, current_user, group_uuid, recurring_uuid)

@cron_router.post("/generate")
async def generate_due(db: AsyncSession = Depends(get_session), x_cron_secret: Optional[str] = Header(default=None)):
    if settings.CRON_SECRET and x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing cron secret.")
    return await service.generate_due(db)

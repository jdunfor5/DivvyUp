from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.expense import ExpenseCreate, ExpenseRead, ExpenseSplitRead, ExpenseUpdate
from ..services import expenses as service

router = APIRouter(
    tags=["expenses"],
    prefix="/groups/{group_uuid}/expenses"
)

@router.post("/", response_model=ExpenseRead)
async def create(group_uuid: UUID, request: ExpenseCreate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create(db=db, current_user=current_user, group_uuid=group_uuid, request=request)

@router.get("/", response_model=list[ExpenseRead])
async def read_all(group_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_all(db=db, current_user=current_user, group_uuid=group_uuid)

@router.get("/{expense_uuid}", response_model=ExpenseRead)
async def read(group_uuid: UUID, expense_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read(db=db, current_user=current_user, group_uuid=group_uuid, expense_uuid=expense_uuid)

@router.get("/{expense_uuid}/splits", response_model=list[ExpenseSplitRead])
async def read_splits(group_uuid: UUID, expense_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_splits(db=db, current_user=current_user, group_uuid=group_uuid, expense_uuid=expense_uuid)

@router.patch("/{expense_uuid}", response_model=ExpenseRead)
async def update(group_uuid: UUID, expense_uuid: UUID, request: ExpenseUpdate, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.update(db=db, current_user=current_user, group_uuid=group_uuid, expense_uuid=expense_uuid, request=request)

@router.delete("/{expense_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(group_uuid: UUID, expense_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete(db=db, current_user=current_user, group_uuid=group_uuid, expense_uuid=expense_uuid)
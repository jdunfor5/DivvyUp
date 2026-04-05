from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from ..services import expenses as service

router = APIRouter(
    tags=["expenses"],
    prefix="/groups/{group_uuid}/expenses"
)

# POST: Create expense endpoint (with participants)
@router.post("/")
async def create(request: ExpenseCreate, db: AsyncSession = Depends(get_session)):
    return await service.create(db=db, request=request)

# GET: Read expenses for group endpoint (i understand this as read all)
@router.get("/", response_model=list[ExpenseRead])
async def read_all(group_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read_all(db=db, group_uuid=group_uuid)

# PATCH: Update expense endpoint
@router.patch("/{expense_uuid}", response_model=ExpenseUpdate)
async def update(expense_uuid: UUID, request: ExpenseUpdate, db: AsyncSession = Depends(get_session)):
    return await service.update(db=db, expense_uuid=expense_uuid, request=request)

# DELETE: Delete expense endpoint
@router.delete("/{expense_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(expense_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.delete(db=db, expense_uuid=expense_uuid)

# UNKNOWN: Handle different split types (equal, custom amounts, percentages)
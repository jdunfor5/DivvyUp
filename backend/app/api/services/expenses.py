from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.expense import Expense, ExpenseCreate, ExpenseUpdate

# TODO:
# 
# POST: Create expense endpoint (with participants)
async def create(db: AsyncSession, request: ExpenseCreate):
    new_expense = Expense(
        group_id        = request.group_id,
        paid_by         = request.paid_by,
        description     = request.description,
        amount          = request.amount,
        currency        = request.currency,
        base_amount     = request.base_amount,
        exchange_rate   = request.exchange_rate,
        category_id     = request.category_id,
        split_type      = request.split_type,
        expense_date    = request.expense_date,
        notes           = request.notes
    )

    try:
        db.add(new_expense)
        await db.commit()
        await db.refresh(new_expense)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Expense created successfully"}

# TODO:
# 
# GET: Read expenses for group endpoint (i understand this as read all)
async def read_all(db: AsyncSession, group_uuid: UUID):
    try:
        statement = select(Expense).where(Expense.group_id == group_uuid)
        result = await db.execute(statement)
        expenses = result.scalars().all()

        if not expenses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Expenses for {group_uuid} not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return expenses

# TODO:
# 
# PATCH: Update expense endpoint
async def update(db: AsyncSession, expense_uuid: UUID, request: ExpenseUpdate):
    try:
        statement = select(Expense).where(Expense.id == expense_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")


        update_expense = request.model_dump(exclude_unset=True)

        for field, value in update_expense.items():
            setattr(expense, field, value)

        await db.commit()
        await db.refresh(expense)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return expense

# TODO:
# 
# DELETE: Delete expense endpoint
async def delete(db: AsyncSession, expense_uuid: UUID):
    try:
        statement = select(Expense).where(Expense.id == expense_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        
        await db.delete(expense)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Expense deleted successfully"}

# TODO:
# 
# UNKNOWN: Handle different split types (equal, custom amounts, percentages)
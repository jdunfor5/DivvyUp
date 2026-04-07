from uuid import UUID
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_DOWN
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.recurring import RecurringExpense, RecurringExpenseCreate, RecurringExpenseUpdate, RecurrenceInterval
from ...models.expense import Expense, ExpenseSplit
from ...models.group import GroupMember, GroupMemberRole
from ...models.user import UserRead


def _advance_date(current: date, interval: RecurrenceInterval) -> date:
    if interval == RecurrenceInterval.daily:
        return current + relativedelta(days=1)
    elif interval == RecurrenceInterval.weekly:
        return current + relativedelta(weeks=1)
    elif interval == RecurrenceInterval.biweekly:
        return current + relativedelta(weeks=2)
    elif interval == RecurrenceInterval.monthly:
        return current + relativedelta(months=1)
    elif interval == RecurrenceInterval.yearly:
        return current + relativedelta(years=1)


async def create(db: AsyncSession, current_user: UserRead, group_uuid: UUID, request: RecurringExpenseCreate):
    try:
        result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        new_recurring = RecurringExpense(
            group_id        = group_uuid,
            description     = request.description,
            amount          = request.amount,
            currency        = request.currency,
            base_amount     = request.base_amount,
            exchange_rate   = request.exchange_rate,
            category_id     = request.category_id,
            paid_by         = current_user.id,
            split_type      = request.split_type,
            interval        = request.interval,
            start_date      = request.start_date,
            end_date        = request.end_date,
            next_due_date   = request.start_date,
            created_by      = current_user.id,
        )

        db.add(new_recurring)
        await db.commit()
        await db.refresh(new_recurring)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return new_recurring


async def read_all(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring_expenses = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return recurring_expenses


async def read(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{recurring_uuid} is an invalid recurring expense identifier.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return recurring


async def update(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID, request: RecurringExpenseUpdate):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{recurring_uuid} is an invalid recurring expense identifier.")

        is_creator = recurring.created_by == current_user.id
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        is_admin = member and member.role == GroupMemberRole.admin

        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator or a group admin can update a recurring expense.")

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(recurring, field, value)

        await db.commit()
        await db.refresh(recurring)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return recurring


async def deactivate(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{recurring_uuid} is an invalid recurring expense identifier.")

        is_creator = recurring.created_by == current_user.id
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        is_admin = member and member.role == GroupMemberRole.admin

        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator or a group admin can deactivate a recurring expense.")

        recurring.is_active = False
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None


async def generate_due(db: AsyncSession):
    """Called by the Render cron job. Generates expenses for all due recurring expenses."""
    today = date.today()
    generated = 0

    try:
        statement = select(RecurringExpense).where(
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date <= today
        )
        result = await db.execute(statement)
        due = result.scalars().all()

        for recurring in due:
            if recurring.end_date and today > recurring.end_date:
                recurring.is_active = False
                continue

            new_expense = Expense(
                group_id        = recurring.group_id,
                paid_by         = recurring.paid_by,
                description     = recurring.description,
                amount          = recurring.amount,
                currency        = recurring.currency,
                base_amount     = recurring.base_amount,
                exchange_rate   = recurring.exchange_rate,
                category_id     = recurring.category_id,
                split_type      = recurring.split_type,
                expense_date    = recurring.next_due_date,
                recurring_expense_id = recurring.id,
                created_by      = recurring.created_by,
            )
            db.add(new_expense)
            await db.flush()

            # Equal split among group members
            members_result = await db.execute(select(GroupMember).where(GroupMember.group_id == recurring.group_id))
            members = members_result.scalars().all()
            num_members = len(members)

            if num_members > 0:
                share = (recurring.base_amount / num_members).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
                remainder = recurring.base_amount - (share * num_members)

                splits = []
                for member in members:
                    member_share = share + remainder if member.user_id == recurring.paid_by else share
                    splits.append(ExpenseSplit(
                        expense_id   = new_expense.id,
                        user_id      = member.user_id,
                        share_amount = member_share,
                    ))
                db.add_all(splits)

            recurring.last_generated_date = today
            recurring.next_due_date = _advance_date(recurring.next_due_date, recurring.interval)
            generated += 1

        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

    return {"message": f"Generated {generated} expense(s)."}

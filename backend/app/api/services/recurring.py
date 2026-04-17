from uuid import UUID
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.recurring import RecurringExpense, RecurringExpenseSplit, RecurringExpenseCreate, RecurringExpenseUpdate, RecurrenceInterval, MemberSplit, SplitType
from ...models.expense import Expense, ExpenseSplit
from ...models.group import GroupMember, GroupMemberRole
from ...models.user import UserRead
from ...dependencies.logging import get_logger
from .expenses import _build_splits

logger = get_logger(__name__)


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

        if request.split_type != SplitType.equal and request.member_splits:
            db.add_all(_build_recurring_splits(new_recurring.id, request.member_splits, request.split_type))
            await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error creating recurring expense in group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return new_recurring


async def read_all(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring_expenses = result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("Database error reading recurring expenses for group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return recurring_expenses


async def read_splits(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")
        result = await db.execute(select(RecurringExpenseSplit).where(RecurringExpenseSplit.recurring_expense_id == recurring_uuid))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("Database error reading splits for recurring expense %s: %s", recurring_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")


async def read(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found.")
    except SQLAlchemyError as e:
        logger.warning("Database error reading recurring expense %s: %s", recurring_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return recurring


async def update(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID, request: RecurringExpenseUpdate):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found.")

        is_creator = recurring.created_by == current_user.id
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        is_admin = member and member.role == GroupMemberRole.admin

        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator or a group admin can update a recurring expense.")

        patch = request.model_dump(exclude_unset=True, exclude={"member_splits"})
        for field, value in patch.items():
            setattr(recurring, field, value)

        if "split_type" in patch or request.member_splits is not None:
            await db.execute(sa_delete(RecurringExpenseSplit).where(RecurringExpenseSplit.recurring_expense_id == recurring_uuid))
            effective_split = recurring.split_type
            if request.member_splits and effective_split != SplitType.equal:
                db.add_all(_build_recurring_splits(recurring_uuid, request.member_splits, effective_split))

        await db.commit()
        await db.refresh(recurring)
    except SQLAlchemyError as e:
        logger.warning("Database error updating recurring expense %s: %s", recurring_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return recurring


async def deactivate(db: AsyncSession, current_user: UserRead, group_uuid: UUID, recurring_uuid: UUID):
    try:
        statement = select(RecurringExpense).where(RecurringExpense.id == recurring_uuid, RecurringExpense.group_id == group_uuid)
        result = await db.execute(statement)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found.")

        is_creator = recurring.created_by == current_user.id
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        is_admin = member and member.role == GroupMemberRole.admin

        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator or a group admin can deactivate a recurring expense.")

        recurring.is_active = False
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error deactivating recurring expense %s: %s", recurring_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

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

            members_result = await db.execute(select(GroupMember).where(GroupMember.group_id == recurring.group_id))
            members = members_result.scalars().all()

            if members:
                member_splits = None
                if recurring.split_type != SplitType.equal:
                    splits_result = await db.execute(
                        select(RecurringExpenseSplit).where(RecurringExpenseSplit.recurring_expense_id == recurring.id)
                    )
                    stored = splits_result.scalars().all()
                    logger.info("generate_due: recurring=%s split_type=%s stored_splits=%s", recurring.id, recurring.split_type, [(s.user_id, s.share_amount, s.share_percentage) for s in stored])
                    member_splits = [
                        MemberSplit(user_id=s.user_id, amount=s.share_amount, percentage=s.share_percentage)
                        for s in stored
                    ]
                    logger.info("generate_due: member_splits=%s", [(ms.user_id, ms.amount, ms.percentage) for ms in member_splits])
                db.add_all(_build_splits(new_expense.id, members, recurring.base_amount, recurring.paid_by, recurring.split_type, member_splits))

            recurring.last_generated_date = today
            recurring.next_due_date = _advance_date(recurring.next_due_date, recurring.interval)
            generated += 1

        await db.commit()
    except SQLAlchemyError as e:
        logger.error("Database error generating due recurring expenses: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred")

    return {"message": f"Generated {generated} expense(s)."}


def _build_recurring_splits(recurring_id: UUID, member_splits: list[MemberSplit], split_type: SplitType) -> list:
    splits = []
    for s in member_splits:
        splits.append(RecurringExpenseSplit(
            recurring_expense_id=recurring_id,
            user_id=s.user_id,
            share_amount=s.amount if split_type == SplitType.exact else None,
            share_percentage=s.percentage if split_type == SplitType.percentage else None,
        ))
    return splits

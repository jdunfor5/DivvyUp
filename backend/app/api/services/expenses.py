from uuid import UUID
from decimal import Decimal, ROUND_DOWN
from fastapi import HTTPException, status
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.expense import Expense, ExpenseCreate, ExpenseUpdate, ExpenseSplit, MemberSplit
from ...models.recurring import SplitType
from ...models.group import GroupMember, GroupMemberRole
from ...models.user import User, UserRead


async def create(db: AsyncSession, current_user: UserRead, group_uuid: UUID, request: ExpenseCreate):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        new_expense = Expense(
            group_id        = group_uuid,
            paid_by         = current_user.id,
            description     = request.description,
            amount          = request.amount,
            currency        = request.currency,
            base_amount     = request.base_amount,
            exchange_rate   = request.exchange_rate,
            category_id     = request.category_id,
            split_type      = request.split_type,
            expense_date    = request.expense_date,
            notes           = request.notes,
            created_by      = current_user.id
        )

        db.add(new_expense)
        await db.commit()
        await db.refresh(new_expense)

        result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid))
        members = result.scalars().all()

        if not members:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No members found in group.")

        db.add_all(_build_splits(new_expense.id, members, request.base_amount, current_user.id, request.split_type, request.member_splits))
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return new_expense


async def read_all(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        statement = (
            select(Expense, User.display_name)
            .join(User, User.id == Expense.paid_by)
            .where(Expense.group_id == group_uuid, Expense.is_deleted == False)
        )
        result = await db.execute(statement)
        rows = result.all()
        expenses = []
        for expense, paid_by_name in rows:
            d = {c.key: getattr(expense, c.key) for c in expense.__table__.columns}
            d["paid_by_name"] = paid_by_name
            expenses.append(d)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return expenses


async def read(db: AsyncSession, current_user: UserRead, group_uuid: UUID, expense_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        expense = await db.scalar(select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid, Expense.is_deleted == False))
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{expense_uuid} is an invalid expense identifier.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return expense


async def read_splits(db: AsyncSession, current_user: UserRead, group_uuid: UUID, expense_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        expense = await db.scalar(select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid))
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{expense_uuid} is an invalid expense identifier.")

        result = await db.execute(select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_uuid))
        splits = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return splits


async def update(db: AsyncSession, current_user: UserRead, group_uuid: UUID, expense_uuid: UUID, request: ExpenseUpdate):
    try:
        statement = select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{expense_uuid} is an invalid expense identifier.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()

        is_creator = expense.created_by == current_user.id
        is_admin = member and member.role == GroupMemberRole.admin
        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the expense creator or a group admin can update this expense.")

        patch = request.model_dump(exclude_unset=True, exclude={"member_splits"})
        for field, value in patch.items():
            setattr(expense, field, value)

        if "base_amount" in patch or "split_type" in patch or "member_splits" in patch:
            await db.execute(sa_delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_uuid))
            members_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid))
            members = members_result.scalars().all()
            db.add_all(_build_splits(expense.id, members, expense.base_amount, expense.paid_by, expense.split_type, request.member_splits))

        await db.commit()
        await db.refresh(expense)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return expense


async def delete(db: AsyncSession, current_user: UserRead, group_uuid: UUID, expense_uuid: UUID):
    try:
        statement = select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{expense_uuid} is an invalid expense identifier.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()

        is_creator = expense.created_by == current_user.id
        is_admin = member and member.role == GroupMemberRole.admin
        if not is_creator and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the expense creator or a group admin can delete this expense.")

        expense.is_deleted = True
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None


def _build_splits(
    expense_id: UUID,
    members: list,
    base_amount: Decimal,
    payer_id: UUID,
    split_type: SplitType = SplitType.equal,
    member_splits: list[MemberSplit] | None = None,
) -> list:
    if len(members) < 2:
        raise ValueError("Group must have at least 2 members to split an expense.")

    base = Decimal(str(base_amount)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    splits = []

    if split_type == SplitType.equal:
        num_debtors = len(members) - 1
        share = (base / num_debtors).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        remainder = base - (share * num_debtors)
        for member in members:
            if member.user_id == payer_id:
                member_share = Decimal("0.00")
            else:
                member_share = share
                if remainder > 0:
                    member_share += remainder
                    remainder = Decimal("0.00")
            splits.append(ExpenseSplit(expense_id=expense_id, user_id=member.user_id, share_amount=member_share))

    elif split_type == SplitType.exact:
        lookup = {s.user_id: (s.amount or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_DOWN) for s in (member_splits or [])}
        for member in members:
            member_share = Decimal("0.00") if member.user_id == payer_id else lookup.get(member.user_id, Decimal("0.00"))
            splits.append(ExpenseSplit(expense_id=expense_id, user_id=member.user_id, share_amount=member_share))

    elif split_type == SplitType.percentage:
        lookup = {s.user_id: s.percentage or Decimal("0") for s in (member_splits or [])}
        for member in members:
            if member.user_id == payer_id:
                member_share = Decimal("0.00")
            else:
                pct = lookup.get(member.user_id, Decimal("0"))
                member_share = (base * pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            splits.append(ExpenseSplit(expense_id=expense_id, user_id=member.user_id, share_amount=member_share))

    return splits
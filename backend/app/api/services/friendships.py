from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User, UserRead
from ...models.friendship import Friendship
from ...models.expense import Expense, ExpenseSplit
from ...models.settlement import Settlement, PaymentStatus
from ...models.group import GroupMember
from ...dependencies.logging import get_logger

logger = get_logger(__name__)


async def add_friend(db: AsyncSession, current_user: UserRead, friend_uuid: UUID):
    try:
        if current_user.id == friend_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot add yourself as a friend.")

        friend_result = await db.execute(select(User).where(User.id == friend_uuid))
        if not friend_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        existing = await db.execute(select(Friendship).where(Friendship.user_id == current_user.id, Friendship.friend_id == friend_uuid))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already in your friends list.")

        db.add(Friendship(user_id=current_user.id, friend_id=friend_uuid))
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error adding friend %s: %s", friend_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return {"message": f"{friend_uuid} has been added to your friends list."}


async def list_friends(db: AsyncSession, current_user: UserRead):
    try:
        result = await db.execute(
            select(User, Friendship.created_at)
            .join(Friendship, User.id == Friendship.friend_id)
            .where(Friendship.user_id == current_user.id)
        )
        rows = result.all()

        my_groups = await db.execute(select(GroupMember.group_id).where(GroupMember.user_id == current_user.id))
        my_group_ids = {row[0] for row in my_groups.all()}

        friends = []
        for user, added_at in rows:
            friend_groups = await db.execute(select(GroupMember.group_id).where(GroupMember.user_id == user.id))
            shared_group_ids = [str(row[0]) for row in friend_groups.all() if row[0] in my_group_ids]

            balance = await _calculate_balance(db, current_user.id, user.id)
            total_sent = await _calculate_total_sent(db, current_user.id, user.id)
            total_received = await _calculate_total_sent(db, user.id, current_user.id)
            friends.append({
                "id":               user.id,
                "email":            user.email,
                "display_name":     user.display_name,
                "avatar_emoji":     user.avatar_emoji,
                "added_at":         added_at,
                "balance":          balance,
                "total_sent":       total_sent,
                "total_received":   total_received,
                "shared_group_ids": shared_group_ids,
            })
    except SQLAlchemyError as e:
        logger.warning("Database error listing friends for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return friends


async def get_friend(db: AsyncSession, current_user: UserRead, friend_uuid: UUID):
    try:
        result = await db.execute(
            select(User, Friendship.created_at)
            .join(Friendship, User.id == Friendship.friend_id)
            .where(Friendship.user_id == current_user.id, Friendship.friend_id == friend_uuid)
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend not found.")

        user, added_at = row
        balance = await _calculate_balance(db, current_user.id, user.id)
    except SQLAlchemyError as e:
        logger.warning("Database error getting friend %s: %s", friend_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return {
        "id":           user.id,
        "email":        user.email,
        "display_name": user.display_name,
        "avatar_emoji":   user.avatar_emoji,
        "added_at":     added_at,
        "balance":      balance,
    }


async def remove_friend(db: AsyncSession, current_user: UserRead, friend_uuid: UUID):
    try:
        result = await db.execute(select(Friendship).where(Friendship.user_id == current_user.id, Friendship.friend_id == friend_uuid))
        friendship = result.scalar_one_or_none()
        if not friendship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend not found.")

        await db.delete(friendship)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error removing friend %s: %s", friend_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None


async def _calculate_balance(db: AsyncSession, user_id: UUID, friend_id: UUID) -> Decimal:
    """
    Positive  = friend owes current_user
    Negative  = current_user owes friend
    """
    my_groups = await db.execute(select(GroupMember.group_id).where(GroupMember.user_id == user_id))
    my_group_ids = {row[0] for row in my_groups.all()}

    friend_groups = await db.execute(select(GroupMember.group_id).where(GroupMember.user_id == friend_id))
    shared_group_ids = {row[0] for row in friend_groups.all()} & my_group_ids

    balance = Decimal("0")

    for group_id in shared_group_ids:
        result = await db.execute(
            select(ExpenseSplit.share_amount)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .where(
                Expense.group_id == group_id,
                Expense.paid_by == user_id,
                Expense.is_deleted == False,
                ExpenseSplit.user_id == friend_id,
            )
        )
        for (share,) in result.all():
            balance += share

        result = await db.execute(
            select(ExpenseSplit.share_amount)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .where(
                Expense.group_id == group_id,
                Expense.paid_by == friend_id,
                Expense.is_deleted == False,
                ExpenseSplit.user_id == user_id,
            )
        )
        for (share,) in result.all():
            balance -= share

    sent = await db.execute(
        select(Settlement.amount).where(
            Settlement.payer_id == user_id,
            Settlement.payee_id == friend_id,
            Settlement.status == PaymentStatus.completed,
        )
    )
    for (amount,) in sent.all():
        balance += amount  # user paid friend → reduces user's debt → balance increases

    received = await db.execute(
        select(Settlement.amount).where(
            Settlement.payer_id == friend_id,
            Settlement.payee_id == user_id,
            Settlement.status == PaymentStatus.completed,
        )
    )
    for (amount,) in received.all():
        balance -= amount  # friend paid user → reduces friend's debt → balance decreases

    return balance.quantize(Decimal("0.01"))


async def _calculate_total_sent(db: AsyncSession, user_id: UUID, friend_id: UUID) -> Decimal:
    result = await db.execute(
        select(Settlement.amount).where(
            Settlement.payer_id == user_id,
            Settlement.payee_id == friend_id,
            Settlement.status == PaymentStatus.completed,
        )
    )
    return sum((amount for (amount,) in result.all()), Decimal("0")).quantize(Decimal("0.01"))

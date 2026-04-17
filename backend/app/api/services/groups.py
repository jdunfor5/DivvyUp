from uuid import UUID
from decimal import Decimal
from collections import defaultdict
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User, UserRead
from ...models.group import Group, GroupCreate, GroupUpdate, GroupMember, GroupMemberRole
from ...models.expense import Expense, ExpenseSplit
from ...models.settlement import Settlement, PaymentStatus
from ...dependencies.logging import get_logger

logger = get_logger(__name__)


async def create_group(db: AsyncSession, current_user: UserRead, request: GroupCreate):
    new_group = Group(
        name            = request.name,
        description     = request.description,
        base_currency   = request.base_currency,
        created_by      = current_user.id
    )

    try:
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)

        new_group_member = GroupMember(
            group_id        = new_group.id,
            user_id         = new_group.created_by,
            role            = GroupMemberRole.admin
        )

        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        logger.warning("Database error creating group: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return new_group


async def join_group_by_invite(db: AsyncSession, current_user: UserRead, invite_code: str):
    try:
        group_result = await db.execute(select(Group).where(Group.invite_code == invite_code))
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code.")

        existing = await db.execute(select(GroupMember).where(GroupMember.group_id == group.id, GroupMember.user_id == current_user.id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already a member of this group.")

        new_member = GroupMember(group_id=group.id, user_id=current_user.id, role=GroupMemberRole.member)
        db.add(new_member)
        await db.commit()
        await db.refresh(group)
    except SQLAlchemyError as e:
        logger.warning("Database error joining group by invite: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group


async def create_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    new_group_member = GroupMember(
        group_id        = group_uuid,
        user_id         = current_user.id,
        role            = GroupMemberRole.member
    )

    try:
        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        logger.warning("Database error adding member to group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return {"message": f"User has been added to the group."}


async def read_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")
    except SQLAlchemyError as e:
        logger.warning("Database error reading group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group


async def read_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        # Verify the requesting user is a member of the group
        requester_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not requester_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found.")
    except SQLAlchemyError as e:
        logger.warning("Database error reading group member %s in group %s: %s", user_uuid, group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group_member


async def read_group_members(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        statement = (
            select(GroupMember, User.display_name, User.email, User.avatar_emoji)
            .join(User, User.id == GroupMember.user_id)
            .where(GroupMember.group_id == group_uuid)
        )
        result = await db.execute(statement)
        rows = result.all()
        group_members = []
        for member, display_name, email, avatar_emoji in rows:
            group_members.append({
                "group_id": member.group_id,
                "user_id": member.user_id,
                "role": member.role,
                "joined_at": member.joined_at,
                "display_name": display_name,
                "email": email,
                "avatar_emoji": avatar_emoji,
            })
    except SQLAlchemyError as e:
        logger.warning("Database error reading group members for group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group_members


async def read_current_user_groups(db: AsyncSession, current_user: UserRead):
    try:
        statement = (
            select(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .where(GroupMember.user_id == current_user.id)
            .order_by(Group.created_at)
        )
        result = await db.execute(statement)
        groups = result.scalars().all()

    except SQLAlchemyError as e:
        logger.warning("Database error reading groups for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return groups


async def update_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID, request: GroupUpdate):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        if not member or member.role != GroupMemberRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can update the group.")

        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(group, field, value)

        await db.commit()
        await db.refresh(group)
    except SQLAlchemyError as e:
        logger.warning("Database error updating group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return group


async def delete_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        group_result = await db.execute(select(Group).where(Group.id == group_uuid))
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        if not member or member.role != GroupMemberRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can delete the group.")

        await db.delete(group)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error deleting group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None


async def delete_current_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        is_admin = group_member.role == GroupMemberRole.admin
        if is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot remove themselves from the group.")

        await db.delete(group_member)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error removing current user from group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None


async def delete_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        current_group_member = result.scalar_one_or_none()

        if not current_group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        is_self = current_user.id == user_uuid
        if is_self:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot remove yourself from the group. Transfer ownership first.")

        is_admin = current_group_member.role == GroupMemberRole.admin
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an admin of the group to remove someone else.")

        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        targeted_group_member = result.scalar_one_or_none()

        if not targeted_group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in this group.")

        await db.delete(targeted_group_member)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error removing member %s from group %s: %s", user_uuid, group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None


async def transfer_group_ownership(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        current_group_member = result.scalar_one_or_none()

        if not current_group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        if current_group_member.role != GroupMemberRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an admin to transfer ownership.")

        if current_user.id == user_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot transfer ownership to yourself.")

        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        target_group_member = result.scalar_one_or_none()

        if not target_group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not a member of this group.")

        current_group_member.role = GroupMemberRole.member
        target_group_member.role = GroupMemberRole.admin
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error transferring ownership of group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return {"message": f"Ownership of the group has been transferred."}


async def get_balances(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        members_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid))
        members = members_result.scalars().all()

        me = current_user.id
        balances: dict = {m.user_id: Decimal("0") for m in members if m.user_id != me}

        splits_result = await db.execute(
            select(ExpenseSplit, Expense.paid_by)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .where(Expense.group_id == group_uuid, Expense.is_deleted == False)
        )
        for split, paid_by in splits_result.all():
            debtor = split.user_id
            creditor = paid_by
            if debtor == creditor:
                continue

            if creditor == me and debtor in balances:
                balances[debtor] -= split.share_amount
            elif debtor == me and creditor in balances:
                balances[creditor] += split.share_amount

        settlements_result = await db.execute(
            select(Settlement).where(
                Settlement.group_id == group_uuid,
                Settlement.status == PaymentStatus.completed
            )
        )
        for s in settlements_result.scalars().all():
            if s.payer_id == me and s.payee_id in balances:
                balances[s.payee_id] -= s.amount
            elif s.payee_id == me and s.payer_id in balances:
                balances[s.payer_id] += s.amount

    except SQLAlchemyError as e:
        logger.warning("Database error getting balances for group %s: %s", group_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return [{"user_id": uid, "net_balance": bal} for uid, bal in balances.items()]

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

# TODO: Testing
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
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return new_group

# TODO: Testing
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
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

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
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {"message": f"({new_group_member.group_id}, {new_group_member.user_id}) has been added into the \"group_members\" table."}

# TODO: Testing and preconditions
async def read_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return group

# This service function is used to read a group member from a group.
#
# Preconditions:
# - Verify that current user is a valid group member of the group.
# - Verify that the targeted user is a valid group member of the group.
#
# WORK IN PROGRESS
async def read_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the\"group_members\" table. Furthermore, {group_uuid} may be an invalid group identifier. That is, entity does not exist in the \"groups\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group_member

# Read all members of a group
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
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return group_members

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# Would we like this so that only get_current_user can read all groups?
# That is, this function works so long as the supplied user_uuid has at least 1 group that it belongs to as a group member.
async def read_current_user_groups(db: AsyncSession, current_user: UserRead):
    try:
        statement = (
            select(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .where(GroupMember.user_id == current_user.id)
        )
        result = await db.execute(statement)
        groups = result.scalars().all()

    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return groups

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a valid group_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that get_current_user is an admin of the requested group; otherwise, do not update the group!
# As explained with most of the other functions above, currently cannot do this due to create_access_token.
# Additionally, this function throws if one attempts to update all fields due to some kind of database character limit.
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(group, field, value)

        await db.commit()
        await db.refresh(group)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return group

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function is faulty and vulnerable due to the lack of preconditions.
# Assuming there can only be 1 admin (given by whoever created the group).
# Ensure that get_current_user is an admin of the requested group; otherwise, do not delete the group!
# Somewhat cheated and decided to check created_by instead to avoid joining. Likely to change.
# Database throws exception regarding foreign keys remaining if there are other users.
# Solution? Change either created_by or admin to someone else in the group.
async def delete_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        group_result = await db.execute(select(Group).where(Group.id == group_uuid))
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        member = member_result.scalar_one_or_none()
        if not member or member.role != GroupMemberRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can delete the group.")

        await db.delete(group)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None

# This service function is used to delete the currently logged in user from a group.
#
# Preconditions:
# - Verify that the current user is not an admin.
# - Verify that the current user is a valid group member of the group.
async def delete_current_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{current_user.id} is not a group member of {group_uuid}.")
        
        is_admin = group_member.role == GroupMemberRole.admin
        if is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Admins cannot remove themselves from the group.")
        
        await db.delete(group_member)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

# This service function is used to delete members from a group.
#
# Preconditions:
# - Verify that the current user is an admin.
# - Verify that the current user is a valid group member of the group.
# - Verify that the current user is not equal to the requested user.
# - Verify that the requested user to remove is a valid group member of the group.
async def delete_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        current_group_member = result.scalar_one_or_none()

        if not current_group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{current_user.id} is not a group member of {group_uuid}.")
        
        is_self = current_user.id == user_uuid
        if is_self:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You cannot remove yourself from the group. Transfer ownership first.")

        is_admin = current_group_member.role == GroupMemberRole.admin
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You must be an admin of the group to remove someone else.")

        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        targeted_group_member = result.scalar_one_or_none()

        if not targeted_group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the \"group_members\" table. Furthermore, {group_uuid} may be an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        await db.delete(targeted_group_member)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return None


async def transfer_group_ownership(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        current_group_member = result.scalar_one_or_none()

        if not current_group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{current_user.id} is not a group member of {group_uuid}.")

        if current_group_member.role != GroupMemberRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You must be an admin to transfer ownership.")

        if current_user.id == user_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You cannot transfer ownership to yourself.")

        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        target_group_member = result.scalar_one_or_none()

        if not target_group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is not a member of {group_uuid}.")

        current_group_member.role = GroupMemberRole.member
        target_group_member.role = GroupMemberRole.admin
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {"message": f"Ownership of {group_uuid} has been transferred to {user_uuid}."}


async def get_balances(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        members_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid))
        members = members_result.scalars().all()

        # Pairwise balances: how much current_user is owed by (or owes) each other member.
        # Positive = that member owes current_user. Negative = current_user owes that member.
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

            # Only process splits that involve current_user on one side
            if creditor == me and debtor in balances:
                # Someone owes me — their balance goes negative (they owe me)
                balances[debtor] -= split.share_amount
            elif debtor == me and creditor in balances:
                # I owe someone — their balance goes positive (I owe them)
                balances[creditor] += split.share_amount

        settlements_result = await db.execute(
            select(Settlement).where(
                Settlement.group_id == group_uuid,
                Settlement.status == PaymentStatus.completed
            )
        )
        for s in settlements_result.scalars().all():
            # A completed settlement reduces what the payer owes the payee
            if s.payer_id == me and s.payee_id in balances:
                balances[s.payee_id] -= s.amount
            elif s.payee_id == me and s.payer_id in balances:
                balances[s.payer_id] += s.amount

    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return [{"user_id": uid, "net_balance": bal} for uid, bal in balances.items()]

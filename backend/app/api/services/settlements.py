from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.settlement import Settlement, SettlementCreate, PaymentStatus
from ...models.group import GroupMember
from ...models.user import UserRead


async def create(db: AsyncSession, current_user: UserRead, group_uuid: UUID, payee_uuid: UUID, request: SettlementCreate):
    try:
        if current_user.id == payee_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot settle with yourself.")

        result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == payee_uuid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The specified payee is not a member of this group.")

        new_settlement = Settlement(
            group_id        = group_uuid,
            payer_id        = current_user.id,
            payee_id        = payee_uuid,
            amount          = request.amount,
            currency        = request.currency,
            provider        = request.provider,
            provider_ref_id = request.provider_ref_id,
            note            = request.note,
        )

        db.add(new_settlement)
        await db.commit()
        await db.refresh(new_settlement)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return new_settlement


async def read_all(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        statement = select(Settlement).where(Settlement.group_id == group_uuid)
        result = await db.execute(statement)
        settlements = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return settlements


async def read(db: AsyncSession, current_user: UserRead, group_uuid: UUID, settlement_uuid: UUID):
    try:
        member_result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id))
        if not member_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group.")

        result = await db.execute(select(Settlement).where(Settlement.id == settlement_uuid, Settlement.group_id == group_uuid))
        settlement = result.scalar_one_or_none()
        if not settlement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{settlement_uuid} is an invalid settlement identifier.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return settlement


async def confirm(db: AsyncSession, current_user: UserRead, group_uuid: UUID, settlement_uuid: UUID):
    try:
        result = await db.execute(select(Settlement).where(Settlement.id == settlement_uuid, Settlement.group_id == group_uuid))
        settlement = result.scalar_one_or_none()

        if not settlement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{settlement_uuid} is an invalid settlement identifier.")

        if settlement.payee_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the payee can confirm a settlement.")

        if settlement.status != PaymentStatus.pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Settlement is already {settlement.status.value}.")

        settlement.status = PaymentStatus.completed
        settlement.settled_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(settlement)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return settlement


async def cancel(db: AsyncSession, current_user: UserRead, group_uuid: UUID, settlement_uuid: UUID):
    try:
        result = await db.execute(select(Settlement).where(Settlement.id == settlement_uuid, Settlement.group_id == group_uuid))
        settlement = result.scalar_one_or_none()

        if not settlement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{settlement_uuid} is an invalid settlement identifier.")

        if settlement.payer_id != current_user.id and settlement.payee_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the payer or payee can cancel a settlement.")

        if settlement.status != PaymentStatus.pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Settlement is already {settlement.status.value}.")

        settlement.status = PaymentStatus.cancelled
        await db.commit()
        await db.refresh(settlement)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return settlement
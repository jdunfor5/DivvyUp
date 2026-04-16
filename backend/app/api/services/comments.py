from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import UserRead
from ...models.expense import Expense
from ...models.comment import Comment, CommentCreate, CommentRead
from ...dependencies.logging import get_logger

from .helpers import is_user_a_group_member

logger = get_logger(__name__)

async def create_comment(db: AsyncSession, current_user: UserRead, expense_uuid: UUID, group_uuid: UUID, request: CommentCreate):
    try:
        if not await is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user does not have access to the requested group.")

        statement = select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

        new_comment = Comment(
            expense_id      = expense.id,
            user_id         = current_user.id,
            body            = request.body
        )

        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
    except SQLAlchemyError as e:
        logger.warning("Database error creating comment on expense %s: %s", expense_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return new_comment

async def read_comments(db: AsyncSession, current_user: UserRead, expense_uuid: UUID, group_uuid: UUID):
    try:
        if not await is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user does not have access to the requested group.")

        statement = select(Comment).where(Comment.expense_id == expense_uuid)
        result = await db.execute(statement)
        comments = result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("Database error reading comments for expense %s: %s", expense_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return comments

async def read_comment(db: AsyncSession, current_user: UserRead, comment_uuid: UUID, expense_uuid: UUID, group_uuid: UUID):
    try:
        if not await is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user does not have access to the requested group.")

        statement = select(Comment).where(Comment.id == comment_uuid, Comment.expense_id == expense_uuid)
        result = await db.execute(statement)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    except SQLAlchemyError as e:
        logger.warning("Database error reading comment %s: %s", comment_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return comment

async def delete_comment(db: AsyncSession, current_user: UserRead, comment_uuid: UUID, expense_uuid: UUID, group_uuid: UUID):
    try:
        if not await is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user does not have access to the requested group.")

        statement = select(Comment).where(Comment.id == comment_uuid, Comment.expense_id == expense_uuid, Comment.user_id == current_user.id)
        comment = await db.scalar(statement)

        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

        await db.delete(comment)
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("Database error deleting comment %s: %s", comment_uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    return None

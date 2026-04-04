from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import UserRead
from ...models.expense import Expense
from ...models.comment import Comment, CommentCreate, CommentRead

from .helpers import is_user_a_group_member

async def create_comment(db: AsyncSession, current_user: UserRead, expense_uuid: UUID, group_uuid: UUID, request: CommentCreate):
    try:
        if not is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Current user does not have access to the requested group.")
        
        statement = select(Expense).where(Expense.id == expense_uuid, Expense.group_id == group_uuid)
        result = await db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{expense_uuid} is an invalid expense identifier. That is, entity does not exist in the \"expenses\" table. Furthermore, {group_uuid} may be an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        new_comment = Comment(
            expense_id      = expense.id,
            user_id         = current_user.id,
            body            = request.body
        )
        
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {f"{new_comment.id} has been added into the \"comments\" table."}

async def read_comment(db: AsyncSession, current_user: UserRead, comment_uuid: UUID, expense_uuid: UUID, group_uuid: UUID):
    try:
        if not is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Current user does not have access to the requested group.")

        statement = select(Comment).where(Comment.id == comment_uuid, Comment.expense_id == expense_uuid)
        result = await db.execute(statement)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{comment_uuid} is an invalid comment identifier. That is, entity does not exist in the \"comments\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return comment

# NOTE:
# Admins do not have option to delete.
# Believe there is a more efficient way of deleting.
async def delete_comment(db: AsyncSession, current_user: UserRead, comment_uuid: UUID, expense_uuid: UUID, group_uuid: UUID):
    try:
        if not is_user_a_group_member(db, current_user.id, group_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Current user does not have access to the requested group.")

        statement = select(Comment).where(Comment.id == comment_uuid, Comment.expense_id == expense_uuid, Comment.user_id == current_user.id)
        result = await db.scalar(statement)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{comment_uuid} is an invalid comment identifier. That is, entity does not exist in the \"comments\" table.")
        
        await db.delete(comment)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

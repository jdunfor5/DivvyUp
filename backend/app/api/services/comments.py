from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.comment import Comment, CommentCreate, CommentRead

# TODO:
# The user_id expects a UUID to the logged in user.
# The question remains, how do we obtain this UUID?
# It has been set to None momentarily.
#
# POST: Create comment endpoint
async def create(db: AsyncSession, expense_uuid: UUID, request: CommentCreate):
    new_comment = Comment(
        expense_id      = expense_uuid,
        user_id         = None,
        body            = request.body
    )

    try:
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {"Comment created successfully"}

# TODO:
# Security-wise, ensure that user_id can view the requested comment.
# That is, perform a check to determine whether user_id resides in a valid group.
#
# GET: Read comment endpoint
async def read(db: AsyncSession, comment_uuid: UUID):
    try:
        statement = select(Comment).where(Comment.id == comment_uuid)
        result = await db.execute(statement)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return comment

# TODO:
# Security-wise, ensure that user_id can delete the requested comment.
# That is, only the user that created the original comment or the admin of the group.
# The user_id must reside in an appropriate group of where the comment lives.
#
# DELETE: Delete comment endpoint
async def delete(db: AsyncSession, comment_uuid: UUID):
    try:
        statement = select(Comment).where(Comment.id == comment_uuid)
        comment = await db.scalar(statement=statement)

        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        
        await db.delete(comment)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Comment deleted successfully"}
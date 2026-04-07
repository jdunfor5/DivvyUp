from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.comment import CommentCreate, CommentRead
from ..services import comments as service

router = APIRouter(
    tags=["comments"],
    prefix="/groups/{group_uuid}/expenses/{expense_uuid}/comments"
)

@router.post("/")
async def create_comment(request: CommentCreate, group_uuid: UUID, expense_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.create_comment(db, current_user, expense_uuid, group_uuid, request)

@router.get("/", response_model=list[CommentRead])
async def read_comments(group_uuid: UUID, expense_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_comments(db, current_user, expense_uuid, group_uuid)

@router.get("/{comment_uuid}", response_model=CommentRead)
async def read_comment(group_uuid: UUID, expense_uuid: UUID, comment_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.read_comment(db, current_user, comment_uuid, expense_uuid, group_uuid)

@router.delete("/{comment_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(group_uuid: UUID, expense_uuid: UUID, comment_uuid: UUID, current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await service.delete_comment(db, current_user, comment_uuid, expense_uuid, group_uuid)
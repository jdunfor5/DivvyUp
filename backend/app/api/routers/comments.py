from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...models.comment import CommentCreate, CommentRead
from ..services import comments as service

router = APIRouter(
    tags=["comments"],
    prefix="/groups/{group_uuid}/expenses/{expense_uuid}/comments"
)

# POST: Create comment endpoint
@router.post("/")
async def create(request: UserCreate, db: AsyncSession = Depends(get_session)): 
    return await service.create(db=db, request=request)

# GET: Read comment endpoint
@router.get("/{comment_uuid}", response_model=CommentRead)
async def read(user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.read(db=db, user_uuid=user_uuid)

# DELETE: Delete comment endpoint
@router.delete("/{comment_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(user_uuid: UUID, db: AsyncSession = Depends(get_session)):
    return await service.delete(db=db, user_uuid=user_uuid)
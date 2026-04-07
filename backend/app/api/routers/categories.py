from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ...dependencies.security import get_current_user
from ...models.user import UserRead
from ...models.category import CategoryRead, Category

router = APIRouter(
    tags=["categories"],
    prefix="/categories"
)

@router.get("/", response_model=list[CategoryRead])
async def read_all(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Category))
    return result.scalars().all()
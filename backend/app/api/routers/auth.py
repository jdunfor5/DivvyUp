from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from ...dependencies.database import get_session
from ..services import auth as service

router = APIRouter(
    tags=["auth"],
    prefix="/auth"
)

# POST: Login endpoint — returns a JWT access token
@router.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    return await service.login(db=db, form=form)
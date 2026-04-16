from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import User
from ...dependencies.security import verify_password, create_access_token
from ...dependencies.logging import get_logger

logger = get_logger(__name__)

# POST: Login endpoint
async def login(db: AsyncSession, form: OAuth2PasswordRequestForm):
    try:
        statement = select(User).where(User.email == form.username)
        result = await db.execute(statement)
        user = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.warning("Database error during login for %s: %s", form.username, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occurred")

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}

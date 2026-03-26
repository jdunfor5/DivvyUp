from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.notification import Notification

# CAUTION:
# There is currently no create endpoint for notifications as it is believed to only
# create said notifications under certain cirumstances. That is, the model is created within other
# endpoints?

# TODO:
# Security-wise, user_uuid should check against logged in user.
# Additionally, it may be unnecessary to pass user_uuid as a parameter since only the logged in user should read.
# For that purpose, a proper endpoint for the API needs to be established. For reference, go to the respective router. 
# 
# GET: Read notification endpoint
async def read(db: AsyncSession, user_uuid: UUID, notification_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.id == notification_uuid)
        result = await db.execute(statement)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return notification

# TODO:
# Security-wise, user_uuid should check against logged in user.
# Additionally, it may be unnecessary to pass user_uuid as a parameter since only the logged in user should read.
# For that purpose, a proper endpoint for the API needs to be established. For reference, go to the respective router. 
# 
# GET: Read all notification endpoint
async def read_all(db: AsyncSession, user_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.user_id == user_uuid)
        result = await db.execute(statement)
        notifications = result.scalars().all()
        
        if not notifications:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notifications for {user_uuid} not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return notifications
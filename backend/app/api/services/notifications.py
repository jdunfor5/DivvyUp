from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.notification import Notification

# NOTE:
# There is currently no endpoint that allows for the creation of notifications as it is believed to only
# create said notifications under certain cirumstances. That is, the model is created within other service functions?
#
# If you would like to test, I recommend that you populate the notifications yourselves through pgAdmin 4 or Swagger.

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a valid user_uuid and notification_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that the supplied user_uuid is equal to get_current_user; otherwise, do not read the notification!
# Not yet implemented due to create_access_token.
async def read_current_user_notification(db: AsyncSession, user_uuid: UUID, notification_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.id == notification_uuid)
        result = await db.execute(statement)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{notification_uuid} is an invalid notification identifier. That is, entity does not exist in the \"notifications\" table. Furthermore, {user_uuid} may be an invalid user identifier. That is, entity does not exist in the \"users\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return notification

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a user_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that the supplied user_uuid is equal to get_current_user; otherwise, do not read the notifications!
# Not yet implemented due to create_access_token.
# Additionally, notifications should still return even if there are none.
# That is, do not throw exceptions if the requested user_uuid does not have notifications.
async def read_current_user_notifications(db: AsyncSession, user_uuid: UUID):
    try:
        statement = select(Notification).where(Notification.user_id == user_uuid)
        result = await db.execute(statement)
        notifications = result.scalars().all()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return notifications

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a user_uuid and notification_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that the supplied user_uuid is equal to get_current_user; otherwise, do not delete the notification!
# Perhaps unnecessary to request a user_uuid argument now that we can just call get_current_user?
# Not removed for now because call to create_access_token is unknown, which is needed to call get_current_user.
async def delete_current_user_notification(db: AsyncSession, user_uuid: UUID, notification_uuid: UUID):
    try:
        statement = delete(Notification).where(Notification.user_id == user_uuid, Notification.id == notification_uuid)
        await db.execute(statement)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a user_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that the supplied user_uuid is equal to get_current_user; otherwise, do not delete the notifications!
# Perhaps unnecessary to request a user_uuid argument now that we can just call get_current_user?
# Not removed for now because call to create_access_token is unknown, which is needed to call get_current_user.
async def delete_current_user_notifications(db: AsyncSession, user_uuid: UUID):
    try:
        statement = delete(Notification).where(Notification.user_id == user_uuid)
        await db.execute(statement)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

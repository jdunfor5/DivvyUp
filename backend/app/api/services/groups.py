from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.group import Group, GroupCreate, GroupUpdate, GroupMember, GroupMemberRole

# TODO:
# Requires the logged in user for setting default group admin and new_group_member.user_id.
# Thus, user_id for new_group_member is set to None.
# Perhaps add a safety check to see whether the new_group was successful before adding new_group_member.
# 
# POST: Create group endpoint
async def create(db: AsyncSession, request: GroupCreate):
    new_group = Group(
        name            = request.name,
        description     = request.description,
        base_currency   = request.base_currency
    )

    new_group_member = GroupMember(
        group_id        = new_group.id,
        user_id         = None,
        role            = GroupMemberRole.admin
    )

    try:
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)

        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Group created successfully"}

# TODO:
# Requires the logged i nuser for setting new_group_member.user_id.
# By default, every new_group_member is not an admin, which is why that field is omitted.
# How does one manage to join a group? Is it purely from the group's invite code?
# Currently, user needs to identify group. See respective router to determine path.
# 
# POST: Create group member endpoint
async def create_member(db: AsyncSession, group_uuid: UUID):
    new_group_member = GroupMember(
        group_id        = group_uuid,
        user_id         = None
    )

    try:
        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Group member created successfully"}

# TODO:
# I believe it is okay for everyone to read group details.
# How else would you be able to share group invites?
# 
# GET: Read group details endpoint
async def read(db: AsyncSession, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group

# TODO:
# Security-wise, verify that logged in user is a part of the requested group.
# If true, they are allowed to view other member details.
# 
# GET: Read group member endpoint
async def read_member(db: AsyncSession, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group_member

# TODO:
# Security-wise, check logged in user.
# Only update the group if the user is a part of the group and is an admin.
# Otherwise, do not bother updating requested group.
# 
# PATCH: Update group endpoint
async def update(db: AsyncSession, group_uuid: UUID, request: GroupUpdate):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        update_group = request.model_dump(exclude_unset=True)

        for field, value in update_group.items():
            setattr(group, field, value)

        await db.commit()
        await db.refresh(group)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group

# TODO:
# Security-wise, check logged in user.
# Only delete the group if the user is a part of the group and is an admin.
# Otherwise, do not bother deleting requested group.
# I propose a change, which is to introduce a new GroupMemberRole constant of owner.
# That way, only the owner can delete it and not admin(s). Why? A group may have multiple admins?
# 
# DELETE: Delete group endpoint
async def delete(db: AsyncSession, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        await db.delete(group)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Group deleted successfully"}

# TODO:
# Security-wise, check logged in user.
# Only delete the group member if the user is a part of the group and is an admin.
# Otherwise, do not bother deleting the requested group member.
# 
# DELETE: Delete group member endpoint
async def delete_member(db: AsyncSession, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")
        
        await db.delete(group_member)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {"Group member deleted successfully"}

# TODO:
# Unsure how to proceed with request.
# How does one obtain user_uuid? We need to determine logged in user.
# Currently, there is no system in place for that.
# 
# GET: Read all groups endpoint (given a user uuid)
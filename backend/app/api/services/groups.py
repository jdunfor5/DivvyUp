from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...models.user import UserRead
from ...models.group import Group, GroupCreate, GroupUpdate, GroupMember, GroupMemberRole

# TODO: Testing
async def create_group(db: AsyncSession, current_user: UserRead, request: GroupCreate):
    new_group = Group(
        name            = request.name,
        description     = request.description,
        base_currency   = request.base_currency,
        created_by      = current_user.id
    )

    try:
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)

        new_group_member = GroupMember(
            group_id        = new_group.id,
            user_id         = new_group.created_by,
            role            = GroupMemberRole.admin
        )

        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {f"{new_group.id} has been added into the \"groups\" table.\n{new_group_member.id} has been added into the \"group_members\" table."}

# TODO: Testing
async def create_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID):    
    new_group_member = GroupMember(
        group_id        = group_uuid,
        user_id         = current_user.id,
        role            = GroupMemberRole.member
    )

    try:
        db.add(new_group_member)
        await db.commit()
        await db.refresh(new_group_member)
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {f"{new_group_member.id} has been added into the \"group_members\" table."}

# TODO: Testing and preconditions
async def read_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="f{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group

# This service function is used to read a group member from a group.
#
# Preconditions:
# - Verify that current user is a valid group member of the group.
# - Verify that the targeted user is a valid group member of the group.
#
# WORK IN PROGRESS
async def read_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the\"group_members\" table. Furthermore, {group_uuid} may be an invalid group identifier. That is, entity does not exist in the \"groups\" table.")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return group_member

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# Would we like this so that only get_current_user can read all groups?
# That is, this function works so long as the supplied user_uuid has at least 1 group that it belongs to as a group member.
async def read_current_user_groups(db: AsyncSession, current_user: UserRead):
    try:
        groups = (
            session.query(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .filter(GroupMember.user_id == current_user.id)
            .all()
        )

        if not groups:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the\"group_members\" table. Furthermore, there are no associated groups in the \"groups\" table for the supplied user identifier!")
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return groups

# TODO:
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function works if supplied with a valid group_uuid, but is vulnerable due to the lack of preconditions.
# That is, ensure that get_current_user is an admin of the requested group; otherwise, do not update the group!
# As explained with most of the other functions above, currently cannot do this due to create_access_token.
# Additionally, this function throws if one attempts to update all fields due to some kind of database character limit.
async def update_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID, request: GroupUpdate):
    try:
        statement = select(Group).where(Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="f{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")
        
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
# backend/dependencies/security.py includes a function: get_current_user
# backend/dependencies/security.py includes a function: create_access_token
#
# This function is faulty and vulnerable due to the lack of preconditions.
# Assuming there can only be 1 admin (given by whoever created the group).
# Ensure that get_current_user is an admin of the requested group; otherwise, do not delete the group!
# Somewhat cheated and decided to check created_by instead to avoid joining. Likely to change.
# Database throws exception regarding foreign keys remaining if there are other users.
# Solution? Change either created_by or admin to someone else in the group.
async def delete_group(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(Group).where(Group.created_by == current_user.id, Group.id == group_uuid)
        result = await db.execute(statement)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="f{group_uuid} is an invalid group identifier. That is, entity does not exist in the \"groups\" table.")
        
        await db.delete(group)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

# This service function is used to delete the currently logged in user from a group.
#
# Preconditions:
# - Verify that the current user is not an admin.
# - Verify that the current user is a valid group member of the group.
async def delete_current_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        group_member = result.scalar_one_or_none()

        if not group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{current_user.id} is not a group member of {group_uuid}.")
        
        is_admin = group_member.role == GroupMemberRole.admin
        if is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Admins cannot remove themselves from the group.")
        
        await db.delete(group_member)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

# This service function is used to delete members from a group.
#
# Preconditions:
# - Verify that the current user is an admin.
# - Verify that the current user is a valid group member of the group.
# - Verify that the current user is not equal to the requested user.
# - Verify that the requested user to remove is a valid group member of the group.
async def delete_group_member(db: AsyncSession, current_user: UserRead, group_uuid: UUID, user_uuid: UUID):
    try:
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == current_user.id)
        result = await db.execute(statement)
        current_group_member = result.scalar_one_or_none()

        if not current_group_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{current_user.id} is not a group member of {group_uuid}.")
        
        is_self = current_user.id == user_uuid
        if not is_self:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You are not authorized to remove yourself.")
        
        is_admin = current_group_member.role == GroupMemberRole.admin
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You must be an admin of the group to remove someone else.")
        
        statement = select(GroupMember).where(GroupMember.group_id == group_uuid, GroupMember.user_id == user_uuid)
        result = await db.execute(statement)
        targeted_group_member = result.scalar_one_or_none()

        if not targeted_group_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{user_uuid} is an invalid user identifier. That is, entity does not exist in the\"group_members\" table. Furthermore, {group_uuid} may be an invalid group identifier. That is, entity does not exist in the \"groups\" table.")

        await db.delete(group_member)
        await db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__["orig"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return None

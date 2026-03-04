import uuid
import random
import string
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.dependencies.database import Base


def generate_invite_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class GroupMemberRole(str, Enum):
    admin = "admin"
    member = "member"


# ── SQLAlchemy Models ─────────────────────────────────────────

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, default=generate_invite_code)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[GroupMemberRole] = mapped_column(SAEnum(GroupMemberRole), nullable=False, default=GroupMemberRole.member)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Pydantic Schemas ──────────────────────────────────────────

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: str = "USD"


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    invite_code: str
    base_currency: str
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None


class GroupMemberRead(BaseModel):
    group_id: uuid.UUID
    user_id: uuid.UUID
    role: GroupMemberRole
    joined_at: datetime

    class Config:
        from_attributes = True
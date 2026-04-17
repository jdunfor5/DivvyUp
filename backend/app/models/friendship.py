import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.dependencies.database import Base


# ── SQLAlchemy Model ──────────────────────────────────────────

class Friendship(Base):
    __tablename__ = "friendships"

    user_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    friend_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Pydantic Schemas ──────────────────────────────────────────

class FriendRead(BaseModel):
    id:               uuid.UUID
    email:            str
    display_name:     str
    avatar_emoji:     str
    added_at:         datetime
    balance:          Decimal  # positive = they owe you, negative = you owe them
    total_sent:       Decimal = Decimal("0")
    total_received:   Decimal = Decimal("0")
    shared_group_ids: list[str] = []

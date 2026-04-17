import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr
from app.dependencies.database import Base

# ── SQLAlchemy Model ──────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(4), nullable=False, default="💩")
    avatar_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#f2e5e7")
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    venmo_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    paypal_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Pydantic Schemas ──────────────────────────────────────────

class UserCreate(BaseModel):
    """Accepted on registration — plain password, not hash."""
    email: EmailStr
    password: str
    display_name: str
    avatar_emoji: str
    phone: Optional[str] = None
    base_currency: str = "USD"


class UserRead(BaseModel):
    """Returned to clients — never exposes password_hash."""
    id: uuid.UUID
    email: str
    display_name: str
    avatar_emoji: str
    avatar_color: str
    phone: Optional[str]
    venmo_handle: Optional[str]
    paypal_email: Optional[str]
    base_currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """All fields optional for PATCH requests."""
    display_name: Optional[str] = None
    avatar_emoji: Optional[str] = None
    avatar_color: Optional[str] = None
    phone: Optional[str] = None
    venmo_handle: Optional[str] = None
    paypal_email: Optional[str] = None
    base_currency: Optional[str] = None
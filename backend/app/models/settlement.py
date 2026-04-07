import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.dependencies.database import Base


class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class PaymentProvider(str, Enum):
    cash = "cash"
    venmo = "venmo"
    paypal = "paypal"
    other = "other"


# ── SQLAlchemy Models ─────────────────────────────────────────

class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    payer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    provider: Mapped[Optional[PaymentProvider]] = mapped_column(SAEnum(PaymentProvider), nullable=True)
    provider_ref_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SettlementSplit(Base):
    __tablename__ = "settlement_splits"

    settlement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("settlements.id", ondelete="CASCADE"), primary_key=True)
    split_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("expense_splits.id", ondelete="CASCADE"), primary_key=True)
    amount_covered: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


# ── Pydantic Schemas ──────────────────────────────────────────

class SettlementCreate(BaseModel):
    amount: Decimal
    currency: str = "USD"
    provider: Optional[PaymentProvider] = None
    provider_ref_id: Optional[str] = None
    note: Optional[str] = None


class SettlementRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    payer_id: uuid.UUID
    payee_id: uuid.UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider: Optional[PaymentProvider]
    provider_ref_id: Optional[str]
    settled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
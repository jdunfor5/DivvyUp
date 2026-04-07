import uuid
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, DateTime, Date, Boolean, Numeric, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.dependencies.database import Base


class SplitType(str, Enum):
    equal = "equal"
    exact = "exact"
    percentage = "percentage"


class RecurrenceInterval(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    yearly = "yearly"


# ── SQLAlchemy Model ──────────────────────────────────────────

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=Decimal("1"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    paid_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    split_type: Mapped[SplitType] = mapped_column(SAEnum(SplitType), nullable=False, default=SplitType.equal)
    interval: Mapped[RecurrenceInterval] = mapped_column(SAEnum(RecurrenceInterval), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_generated_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ── Pydantic Schemas ──────────────────────────────────────────

class RecurringExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    currency: str = "USD"
    base_amount: Decimal
    exchange_rate: Decimal = Decimal("1")
    category_id: int = 1
    split_type: SplitType = SplitType.equal
    interval: RecurrenceInterval
    start_date: date
    end_date: Optional[date] = None


class RecurringExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    base_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    category_id: Optional[int] = None
    split_type: Optional[SplitType] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class RecurringExpenseRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    paid_by: uuid.UUID
    description: str
    amount: Decimal
    currency: str
    category_id: Optional[int]
    split_type: SplitType
    interval: RecurrenceInterval
    start_date: date
    end_date: Optional[date]
    next_due_date: date
    last_generated_date: Optional[date]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
import uuid
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Boolean, Numeric, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.dependencies.database import Base
from app.models.recurring import SplitType


# ── SQLAlchemy Models ─────────────────────────────────────────

class Expense(Base):
    __tablename__ = "expenses"

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
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurring_expense_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("recurring_expenses.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    share_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    share_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 4), nullable=True)
    is_settled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Pydantic Schemas ──────────────────────────────────────────

class ExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    currency: str = "USD"
    base_amount: Decimal
    exchange_rate: Decimal = Decimal("1")
    category_id: int = 1
    split_type: SplitType = SplitType.equal
    expense_date: date
    notes: Optional[str] = None


class ExpenseRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    paid_by: uuid.UUID
    description: str
    amount: Decimal
    currency: str
    base_amount: Decimal
    category_id: Optional[int]
    split_type: SplitType
    expense_date: date
    notes: Optional[str]
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    base_amount: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    category_id: Optional[int] = None
    split_type: Optional[SplitType] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None


class ExpenseSplitRead(BaseModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    share_amount: Decimal
    share_pct: Optional[Decimal]
    is_settled: bool
    settled_at: Optional[datetime]

    class Config:
        from_attributes = True
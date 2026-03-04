from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from app.dependencies.database import Base


# ── SQLAlchemy Model ──────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


# ── Pydantic Schemas ──────────────────────────────────────────

class CategoryRead(BaseModel):
    id: int
    name: str
    icon: Optional[str]

    class Config:
        from_attributes = True
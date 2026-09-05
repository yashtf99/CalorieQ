import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.base import Base


class MealLog(Base):
    __tablename__ = "user_meal_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    food_item_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("food_items.id", ondelete="SET NULL")
    )
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    food_name_snapshot: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity_g: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    energy_kcal: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    carb_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fat_g: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fibre_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    sodium_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

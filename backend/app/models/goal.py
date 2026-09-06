import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constraints import GOAL_CALORIES_GT, GOAL_WEIGHT_GT
from app.orm.base import Base


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(
            f"daily_calories IS NULL OR daily_calories > {GOAL_CALORIES_GT}",
            name="ck_goal_calories",
        ),
        CheckConstraint(
            f"weight_target_kg IS NULL OR weight_target_kg > {GOAL_WEIGHT_GT}",
            name="ck_goal_weight",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    daily_calories: Mapped[float | None] = mapped_column(Numeric(7, 2))
    protein_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    carbs_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fat_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fibre_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    weight_target_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    active_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    active_to: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

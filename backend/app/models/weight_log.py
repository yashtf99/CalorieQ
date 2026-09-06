import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constraints import WEIGHT_LOG_GT, WEIGHT_LOG_LT
from app.orm.base import Base


class WeightLog(Base):
    __tablename__ = "weight_logs"
    __table_args__ = (
        CheckConstraint(
            f"weight_kg > {WEIGHT_LOG_GT} AND weight_kg < {WEIGHT_LOG_LT}",
            name="ck_weight_kg",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    notes: Mapped[str | None] = mapped_column(Text)

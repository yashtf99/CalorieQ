from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constraints import PROFILE_HEIGHT_GT, PROFILE_HEIGHT_LT
from app.orm.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            f"height_cm IS NULL OR (height_cm > {PROFILE_HEIGHT_GT} AND height_cm < {PROFILE_HEIGHT_LT})",
            name="ck_profile_height",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    dob: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(50))
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    activity_level: Mapped[str | None] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

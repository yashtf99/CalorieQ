import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.base import Base


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255))
    energy_kcal: Mapped[float | None] = mapped_column(Numeric(7, 2))
    energy_kj: Mapped[float | None] = mapped_column(Numeric(7, 2))
    protein_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    carb_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fat_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    freesugar_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fibre_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    sfa_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    mufa_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    pufa_g: Mapped[float | None] = mapped_column(Numeric(6, 2))
    cholesterol_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    calcium_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    phosphorus_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    magnesium_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    sodium_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    potassium_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    iron_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    copper_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    selenium_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    chromium_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    manganese_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    molybdenum_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    zinc_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vita_ug: Mapped[float | None] = mapped_column(Numeric(7, 2))
    vite_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitd2_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitd3_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitk1_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitk2_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    folate_ug: Mapped[float | None] = mapped_column(Numeric(7, 2))
    vitb1_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb2_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb3_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb5_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb6_mg: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb7_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitb9_ug: Mapped[float | None] = mapped_column(Numeric(7, 4))
    vitc_mg: Mapped[float | None] = mapped_column(Numeric(7, 2))
    carotenoids_ug: Mapped[float | None] = mapped_column(Numeric(7, 2))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

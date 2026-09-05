from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


GoalType = Literal["lose", "maintain", "gain"]


class GoalIn(BaseModel):
    goal_type: GoalType
    # Numeric(7,2) → max 99999.99; enforce here so we return 400 not 500
    daily_calories: float | None = Field(default=None, gt=0, lt=100_000)
    protein_g: float | None = Field(default=None, ge=0, lt=100_000)
    carbs_g: float | None = Field(default=None, ge=0, lt=100_000)
    fat_g: float | None = Field(default=None, ge=0, lt=100_000)
    fibre_g: float | None = Field(default=None, ge=0, lt=100_000)
    weight_target_kg: float | None = Field(default=None, gt=0, lt=700)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    goal_type: str
    daily_calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fibre_g: float | None
    weight_target_kg: float | None
    active_from: datetime
    active_to: datetime | None
    created_at: datetime

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.constraints import (
    GOAL_CALORIES_GT, GOAL_CALORIES_LT,
    GOAL_MACRO_GE, GOAL_MACRO_LT,
    GOAL_WEIGHT_GT, GOAL_WEIGHT_LT,
    PROFILE_HEIGHT_GT, PROFILE_HEIGHT_LT,
    PROFILE_WEIGHT_GT, PROFILE_WEIGHT_LT,
)

GoalType = Literal["lose", "maintain", "gain"]


class GoalIn(BaseModel):
    goal_type: GoalType
    daily_calories: float | None = Field(default=None, gt=GOAL_CALORIES_GT, lt=GOAL_CALORIES_LT)
    protein_g: float | None = Field(default=None, ge=GOAL_MACRO_GE, lt=GOAL_MACRO_LT)
    carbs_g: float | None = Field(default=None, ge=GOAL_MACRO_GE, lt=GOAL_MACRO_LT)
    fat_g: float | None = Field(default=None, ge=GOAL_MACRO_GE, lt=GOAL_MACRO_LT)
    fibre_g: float | None = Field(default=None, ge=GOAL_MACRO_GE, lt=GOAL_MACRO_LT)
    weight_target_kg: float | None = Field(default=None, gt=GOAL_WEIGHT_GT, lt=GOAL_WEIGHT_LT)


ActivityLevel = Literal["sedentary", "lightly_active", "active", "very_active"]
Gender        = Literal["male", "female", "other", "prefer_not_to_say"]


class GoalSuggestionParams(BaseModel):
    height_cm:      float = Field(gt=PROFILE_HEIGHT_GT, lt=PROFILE_HEIGHT_LT)
    weight_kg:      float = Field(gt=PROFILE_WEIGHT_GT, lt=PROFILE_WEIGHT_LT)
    dob:            str   # YYYY-MM-DD — format + range validated in service
    gender:         Gender
    activity_level: ActivityLevel


class MacroSuggestion(BaseModel):
    daily_calories: int
    protein_g:      int
    carbs_g:        int
    fat_g:          int
    fibre_g:        int


class GoalSuggestionOut(BaseModel):
    bmr:         int
    tdee:        int
    suggestions: dict[str, MacroSuggestion]   # keys: "lose", "maintain", "gain"


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal_type: str
    daily_calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fibre_g: float | None
    weight_target_kg: float | None
    active_from: datetime
    active_to: datetime | None

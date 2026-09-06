from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constraints import (
    MEAL_CARB_GE, MEAL_CARB_LT,
    MEAL_ENERGY_GE, MEAL_ENERGY_LT,
    MEAL_FAT_GE, MEAL_FAT_LT,
    MEAL_FIBRE_GE, MEAL_FIBRE_LT,
    MEAL_PROTEIN_GE, MEAL_PROTEIN_LT,
    MEAL_QUANTITY_GT, MEAL_QUANTITY_LT,
    MEAL_SODIUM_GE, MEAL_SODIUM_LT,
)

MealType   = Literal["breakfast", "lunch", "dinner", "snacks"]
MealSource = Literal["user", "ai"]

_Q = dict(gt=MEAL_QUANTITY_GT, lt=MEAL_QUANTITY_LT)


class MealLogIn(BaseModel):
    meal_type: MealType
    quantity_g: float = Field(**_Q)
    logged_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    food_item_id: str | None = None

    food_name_snapshot: str | None = Field(default=None, min_length=1, max_length=500)
    energy_kcal: float | None = Field(default=None, ge=MEAL_ENERGY_GE, lt=MEAL_ENERGY_LT)
    protein_g: float | None = Field(default=None, ge=MEAL_PROTEIN_GE, lt=MEAL_PROTEIN_LT)
    carb_g: float | None = Field(default=None, ge=MEAL_CARB_GE, lt=MEAL_CARB_LT)
    fat_g: float | None = Field(default=None, ge=MEAL_FAT_GE, lt=MEAL_FAT_LT)
    fibre_g: float | None = Field(default=None, ge=MEAL_FIBRE_GE, lt=MEAL_FIBRE_LT)
    sodium_mg: float | None = Field(default=None, ge=MEAL_SODIUM_GE, lt=MEAL_SODIUM_LT)
    source: MealSource = "user"

    @model_validator(mode="after")
    def check_linked_or_freeform(self) -> "MealLogIn":
        has_item     = self.food_item_id is not None
        has_snapshot = self.food_name_snapshot is not None
        has_kcal     = self.energy_kcal is not None

        if not has_item and not (has_snapshot and has_kcal):
            raise ValueError(
                "Provide either food_item_id (linked) "
                "or food_name_snapshot + energy_kcal (free-form)"
            )
        if has_item and has_snapshot:
            raise ValueError("Provide food_item_id or food_name_snapshot — not both")
        return self


class MealLogPatchIn(BaseModel):
    meal_type: MealType | None = None
    quantity_g: float | None = Field(default=None, **_Q)
    logged_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    energy_kcal: float | None = Field(default=None, ge=MEAL_ENERGY_GE, lt=MEAL_ENERGY_LT)
    protein_g: float | None = Field(default=None, ge=MEAL_PROTEIN_GE, lt=MEAL_PROTEIN_LT)
    carb_g: float | None = Field(default=None, ge=MEAL_CARB_GE, lt=MEAL_CARB_LT)
    fat_g: float | None = Field(default=None, ge=MEAL_FAT_GE, lt=MEAL_FAT_LT)
    fibre_g: float | None = Field(default=None, ge=MEAL_FIBRE_GE, lt=MEAL_FIBRE_LT)
    sodium_mg: float | None = Field(default=None, ge=MEAL_SODIUM_GE, lt=MEAL_SODIUM_LT)


class MealLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    food_item_id: str | None
    food_name_snapshot: str
    meal_type: str
    quantity_g: float
    energy_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fibre_g: float | None
    sodium_mg: float | None
    source: str
    notes: str | None
    logged_at: datetime

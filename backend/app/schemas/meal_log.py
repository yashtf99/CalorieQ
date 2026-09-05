from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MealType = Literal["breakfast", "lunch", "dinner", "snacks"]
MealSource = Literal["user", "ai"]

_Q = dict(gt=0, lt=4_000)


class MealLogIn(BaseModel):
    meal_type: MealType
    quantity_g: float = Field(**_Q)
    logged_at: datetime | None = None          # defaults to now() server-side
    notes: str | None = Field(default=None, max_length=1000)

    # Linked entry — server scales nutrition from food item
    food_item_id: str | None = None

    # Free-form entry — client supplies nutrition directly
    food_name_snapshot: str | None = Field(default=None, min_length=1, max_length=500)
    energy_kcal: float | None = Field(default=None, ge=0, lt=10_000)
    protein_g: float | None = Field(default=None, ge=0, lt=600)
    carb_g: float | None = Field(default=None, ge=0, lt=1_000)
    fat_g: float | None = Field(default=None, ge=0, lt=600)
    fibre_g: float | None = Field(default=None, ge=0, lt=200)
    sodium_mg: float | None = Field(default=None, ge=0, lt=20_000)
    source: MealSource = "user"

    @model_validator(mode="after")
    def check_linked_or_freeform(self) -> "MealLogIn":
        has_item = self.food_item_id is not None
        has_snapshot = self.food_name_snapshot is not None
        has_kcal = self.energy_kcal is not None

        if not has_item and not (has_snapshot and has_kcal):
            raise ValueError(
                "Provide either food_item_id (linked) "
                "or food_name_snapshot + energy_kcal (free-form)"
            )
        if has_item and has_snapshot:
            raise ValueError("Provide food_item_id or food_name_snapshot — not both")
        return self


class MealLogPatchIn(BaseModel):
    """
    For linked entries (food_item_id set): only quantity_g / meal_type / logged_at / notes.
    Macros are recalculated server-side on quantity change.

    For free-form entries (no food_item_id): nutrition fields may also be updated directly.
    """
    meal_type: MealType | None = None
    quantity_g: float | None = Field(default=None, **_Q)
    logged_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    # Free-form overrides (ignored for linked entries)
    energy_kcal: float | None = Field(default=None, ge=0, lt=10_000)
    protein_g: float | None = Field(default=None, ge=0, lt=600)
    carb_g: float | None = Field(default=None, ge=0, lt=1_000)
    fat_g: float | None = Field(default=None, ge=0, lt=600)
    fibre_g: float | None = Field(default=None, ge=0, lt=200)
    sodium_mg: float | None = Field(default=None, ge=0, lt=20_000)


class MealLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
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
    created_at: datetime

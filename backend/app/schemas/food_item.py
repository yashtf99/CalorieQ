from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FoodPortionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    description: str
    gram_weight: float


class FoodItemSearchOut(BaseModel):
    """Lightweight projection returned in search results."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    name: str
    category: str | None
    energy_kcal: float | None
    protein_g: float | None
    carb_g: float | None
    fat_g: float | None
    fibre_g: float | None


class FoodItemDetailOut(FoodItemSearchOut):
    """Full nutrient detail returned on GET /food_items/{id}."""
    energy_kj: float | None
    freesugar_g: float | None
    sfa_g: float | None
    mufa_g: float | None
    pufa_g: float | None
    cholesterol_mg: float | None
    calcium_mg: float | None
    phosphorus_mg: float | None
    magnesium_mg: float | None
    sodium_mg: float | None
    potassium_mg: float | None
    iron_mg: float | None
    copper_mg: float | None
    selenium_ug: float | None
    chromium_mg: float | None
    manganese_mg: float | None
    molybdenum_mg: float | None
    zinc_mg: float | None
    vita_ug: float | None
    vite_mg: float | None
    vitd2_ug: float | None
    vitd3_ug: float | None
    vitk1_ug: float | None
    vitk2_ug: float | None
    folate_ug: float | None
    vitb1_mg: float | None
    vitb2_mg: float | None
    vitb3_mg: float | None
    vitb5_mg: float | None
    vitb6_mg: float | None
    vitb7_ug: float | None
    vitb9_ug: float | None
    vitc_mg: float | None
    carotenoids_ug: float | None
    is_verified: bool
    created_by: str | None
    created_at: datetime
    portions: list[FoodPortionOut] = []


FoodSource = Literal["indb", "usda", "user_custom"]


class CustomFoodItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=255)
    energy_kcal: float = Field(ge=0, lt=10_000)
    protein_g: float | None = Field(default=None, ge=0, lt=600)
    carb_g: float | None = Field(default=None, ge=0, lt=1_000)
    fat_g: float | None = Field(default=None, ge=0, lt=600)
    fibre_g: float | None = Field(default=None, ge=0, lt=200)
    sodium_mg: float | None = Field(default=None, ge=0, lt=20_000)

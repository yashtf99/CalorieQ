from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.constraints import (
    FOOD_CARB_GE, FOOD_CARB_LT,
    FOOD_CHOL_GE, FOOD_CHOL_LT,
    FOOD_ENERGY_GE, FOOD_ENERGY_LT,
    FOOD_ENERGY_KJ_GE, FOOD_ENERGY_KJ_LT,
    FOOD_FAT_GE, FOOD_FAT_LT,
    FOOD_FIBRE_GE, FOOD_FIBRE_LT,
    FOOD_IRON_GE, FOOD_IRON_LT,
    FOOD_MINERAL_GE, FOOD_MINERAL_LT,
    FOOD_POTASSIUM_GE, FOOD_POTASSIUM_LT,
    FOOD_PROTEIN_GE, FOOD_PROTEIN_LT,
    FOOD_SODIUM_GE, FOOD_SODIUM_LT,
    FOOD_TRACE_GE, FOOD_TRACE_LT,
    FOOD_VIT_MG_GE, FOOD_VIT_MG_LT,
    FOOD_VIT_UG_GE, FOOD_VIT_UG_LT,
)


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
    portions: list[FoodPortionOut] = []


class FoodCategoryCount(BaseModel):
    category: str
    count: int


FoodSource = Literal["indb", "usda", "user_custom"]


class CustomFoodItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    energy_kcal: float = Field(ge=FOOD_ENERGY_GE, lt=FOOD_ENERGY_LT)

    category: str | None = Field(default=None, max_length=255)
    energy_kj: float | None = Field(default=None, ge=FOOD_ENERGY_KJ_GE, lt=FOOD_ENERGY_KJ_LT)
    protein_g: float | None = Field(default=None, ge=FOOD_PROTEIN_GE, lt=FOOD_PROTEIN_LT)
    carb_g: float | None = Field(default=None, ge=FOOD_CARB_GE, lt=FOOD_CARB_LT)
    fat_g: float | None = Field(default=None, ge=FOOD_FAT_GE, lt=FOOD_FAT_LT)
    freesugar_g: float | None = Field(default=None, ge=FOOD_CARB_GE, lt=FOOD_CARB_LT)
    fibre_g: float | None = Field(default=None, ge=FOOD_FIBRE_GE, lt=FOOD_FIBRE_LT)
    sfa_g: float | None = Field(default=None, ge=FOOD_FAT_GE, lt=FOOD_FAT_LT)
    mufa_g: float | None = Field(default=None, ge=FOOD_FAT_GE, lt=FOOD_FAT_LT)
    pufa_g: float | None = Field(default=None, ge=FOOD_FAT_GE, lt=FOOD_FAT_LT)
    cholesterol_mg: float | None = Field(default=None, ge=FOOD_CHOL_GE, lt=FOOD_CHOL_LT)

    calcium_mg: float | None = Field(default=None, ge=FOOD_MINERAL_GE, lt=FOOD_MINERAL_LT)
    phosphorus_mg: float | None = Field(default=None, ge=FOOD_MINERAL_GE, lt=FOOD_MINERAL_LT)
    magnesium_mg: float | None = Field(default=None, ge=FOOD_MINERAL_GE, lt=FOOD_MINERAL_LT)
    sodium_mg: float | None = Field(default=None, ge=FOOD_SODIUM_GE, lt=FOOD_SODIUM_LT)
    potassium_mg: float | None = Field(default=None, ge=FOOD_POTASSIUM_GE, lt=FOOD_POTASSIUM_LT)
    iron_mg: float | None = Field(default=None, ge=FOOD_IRON_GE, lt=FOOD_IRON_LT)
    copper_mg: float | None = Field(default=None, ge=FOOD_TRACE_GE, lt=FOOD_TRACE_LT)
    selenium_ug: float | None = Field(default=None, ge=FOOD_MINERAL_GE, lt=FOOD_MINERAL_LT)
    chromium_mg: float | None = Field(default=None, ge=FOOD_TRACE_GE, lt=FOOD_TRACE_LT)
    manganese_mg: float | None = Field(default=None, ge=FOOD_TRACE_GE, lt=FOOD_TRACE_LT)
    molybdenum_mg: float | None = Field(default=None, ge=FOOD_TRACE_GE, lt=FOOD_TRACE_LT)
    zinc_mg: float | None = Field(default=None, ge=FOOD_TRACE_GE, lt=FOOD_TRACE_LT)

    vita_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vite_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitd2_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitd3_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitk1_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitk2_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    folate_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitb1_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitb2_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitb3_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitb5_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitb6_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    vitb7_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitb9_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)
    vitc_mg: float | None = Field(default=None, ge=FOOD_VIT_MG_GE, lt=FOOD_VIT_MG_LT)
    carotenoids_ug: float | None = Field(default=None, ge=FOOD_VIT_UG_GE, lt=FOOD_VIT_UG_LT)

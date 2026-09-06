from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.core.constraints import (
    MEAL_CARB_GE, MEAL_CARB_LT,
    MEAL_ENERGY_GE, MEAL_ENERGY_LT,
    MEAL_FAT_GE, MEAL_FAT_LT,
    MEAL_FIBRE_GE, MEAL_FIBRE_LT,
    MEAL_PROTEIN_GE, MEAL_PROTEIN_LT,
    MEAL_QUANTITY_GT, MEAL_QUANTITY_LT,
    MEAL_SODIUM_GE, MEAL_SODIUM_LT,
)


class ImageExtractionOut(BaseModel):
    """Response from image nutrition extraction endpoint."""

    is_nutrition_label: bool
    quantity_g: Optional[float] = Field(None, gt=MEAL_QUANTITY_GT, lt=MEAL_QUANTITY_LT)
    energy_kcal: Optional[float] = Field(None, ge=MEAL_ENERGY_GE, lt=MEAL_ENERGY_LT)
    protein_g: Optional[float] = Field(None, ge=MEAL_PROTEIN_GE, lt=MEAL_PROTEIN_LT)
    carb_g: Optional[float] = Field(None, ge=MEAL_CARB_GE, lt=MEAL_CARB_LT)
    fat_g: Optional[float] = Field(None, ge=MEAL_FAT_GE, lt=MEAL_FAT_LT)
    fibre_g: Optional[float] = Field(None, ge=MEAL_FIBRE_GE, lt=MEAL_FIBRE_LT)
    sodium_mg: Optional[float] = Field(None, ge=MEAL_SODIUM_GE, lt=MEAL_SODIUM_LT)

    food_item_name: Optional[str] = None
    confidence: Optional[Literal["low", "medium", "high"]] = None
    estimation_basis: Optional[str] = None

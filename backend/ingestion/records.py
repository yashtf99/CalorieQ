"""Normalised in-memory records shared between adapters and strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FoodItemRecord:
    id:             str
    source:         str
    external_id:    Optional[str]
    name:           str
    category:       Optional[str]
    energy_kcal:    Optional[float]
    energy_kj:      Optional[float]
    protein_g:      Optional[float]
    carb_g:         Optional[float]
    fat_g:          Optional[float]
    freesugar_g:    Optional[float]
    fibre_g:        Optional[float]
    sfa_g:          Optional[float]
    mufa_g:         Optional[float]
    pufa_g:         Optional[float]
    cholesterol_mg: Optional[float]
    calcium_mg:     Optional[float]
    phosphorus_mg:  Optional[float]
    magnesium_mg:   Optional[float]
    sodium_mg:      Optional[float]
    potassium_mg:   Optional[float]
    iron_mg:        Optional[float]
    copper_mg:      Optional[float]
    selenium_ug:    Optional[float]
    chromium_mg:    Optional[float]
    manganese_mg:   Optional[float]
    molybdenum_mg:  Optional[float]
    zinc_mg:        Optional[float]
    vita_ug:        Optional[float]
    vite_mg:        Optional[float]
    vitd2_ug:       Optional[float]
    vitd3_ug:       Optional[float]
    vitk1_ug:       Optional[float]
    vitk2_ug:       Optional[float]
    folate_ug:      Optional[float]
    vitb1_mg:       Optional[float]
    vitb2_mg:       Optional[float]
    vitb3_mg:       Optional[float]
    vitb5_mg:       Optional[float]
    vitb6_mg:       Optional[float]
    vitb7_ug:       Optional[float]
    vitb9_ug:       Optional[float]
    vitc_mg:        Optional[float]
    carotenoids_ug: Optional[float]
    is_verified:    bool            = True
    created_by:     Optional[str]   = None


@dataclass
class FoodPortionRecord:
    id:           str
    food_item_id: str
    description:  str
    gram_weight:  float

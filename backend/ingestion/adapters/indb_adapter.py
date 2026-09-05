"""
INDBAdapter — converts INDB-processed/indb.csv DataFrame to normalised records.

Key transformations:
  - sfa_mg / mufa_mg / pufa_mg are stored in mg in INDB → divide by 1000 to get grams
  - Column renames to match food_items schema
  - servings_unit column is dropped (no gram weight available, cannot map to food_portions)
"""
from __future__ import annotations

import uuid

import pandas as pd

from ..base import FoodDataAdapter
from ..records import FoodItemRecord


class INDBAdapter(FoodDataAdapter):

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def adapt_food_items(self) -> list[FoodItemRecord]:
        df = self._df.copy()

        # INDB stores sfa/mufa/pufa in mg; schema expects grams
        for col in ("sfa_mg", "mufa_mg", "pufa_mg"):
            df[col] = df[col] / 1000

        df = df.rename(columns={
            "food_code":     "external_id",
            "food_name":     "name",
            "primarysource": "category",
            "sfa_mg":        "sfa_g",
            "mufa_mg":       "mufa_g",
            "pufa_mg":       "pufa_g",
        })

        df["id"]          = [str(uuid.uuid4()) for _ in range(len(df))]
        df["source"]      = "indb"
        df["is_verified"] = True
        df["created_by"]  = None

        df = df.drop(columns=["servings_unit"], errors="ignore")

        fields_order = [
            "id", "source", "external_id", "name", "category",
            "energy_kcal", "energy_kj", "protein_g", "carb_g", "fat_g",
            "freesugar_g", "fibre_g", "sfa_g", "mufa_g", "pufa_g",
            "cholesterol_mg", "calcium_mg", "phosphorus_mg", "magnesium_mg",
            "sodium_mg", "potassium_mg", "iron_mg", "copper_mg", "selenium_ug",
            "chromium_mg", "manganese_mg", "molybdenum_mg", "zinc_mg",
            "vita_ug", "vite_mg", "vitd2_ug", "vitd3_ug", "vitk1_ug", "vitk2_ug",
            "folate_ug", "vitb1_mg", "vitb2_mg", "vitb3_mg", "vitb5_mg",
            "vitb6_mg", "vitb7_ug", "vitb9_ug", "vitc_mg", "carotenoids_ug",
            "is_verified", "created_by",
        ]
        df = df.reindex(columns=fields_order)

        return [
            FoodItemRecord(**{k: (None if pd.isna(v) else v) for k, v in row.items()})
            for row in df.to_dict("records")
        ]

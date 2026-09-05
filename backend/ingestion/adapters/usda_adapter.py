"""
USDAAdapter — converts USDA SR Legacy DataFrames to normalised records.

Inputs (passed by USDAIngestionStrategy):
  foods_df         : fdc_id, description, category  (already joined with food_category)
  food_nutrients_df: fdc_id, nutrient_id, amount    (filtered to sr_legacy fdc_ids)
  food_portions_df : fdc_id, amount, measure_unit_id, portion_description, modifier, gram_weight
  measure_units_df : id, name

Key transformations:
  - Long-format food_nutrients pivoted to wide format keyed on fdc_id
  - chromium  (nutrient 1096, µg) → chromium_mg  (÷ 1000)
  - molybdenum(nutrient 1102, µg) → molybdenum_mg(÷ 1000)
  - carotenoids_ug = sum of beta-carotene(1107) + alpha-carotene(1108)
                         + lycopene(1122) + lutein+zeaxanthin(1123)
  - energy_kj derived from energy_kcal × 4.184  (USDA has no kJ nutrient)
  - freesugar_g = NULL  (no USDA equivalent)
  - adapt_food_items() and adapt_portions() share one lazy transformation pass
"""
from __future__ import annotations

import uuid
from typing import Optional

import pandas as pd

from ..base import FoodDataAdapter
from ..records import FoodItemRecord, FoodPortionRecord

# nutrient_id → (food_items column name, multiplier to reach stored unit)
_NUTRIENT_MAP: dict[int, tuple[str, float]] = {
    1008: ("energy_kcal",    1.0),
    1003: ("protein_g",      1.0),
    1005: ("carb_g",         1.0),
    1004: ("fat_g",          1.0),
    1079: ("fibre_g",        1.0),
    1258: ("sfa_g",          1.0),
    1292: ("mufa_g",         1.0),
    1293: ("pufa_g",         1.0),
    1253: ("cholesterol_mg", 1.0),
    1087: ("calcium_mg",     1.0),
    1091: ("phosphorus_mg",  1.0),
    1090: ("magnesium_mg",   1.0),
    1093: ("sodium_mg",      1.0),
    1092: ("potassium_mg",   1.0),
    1089: ("iron_mg",        1.0),
    1098: ("copper_mg",      1.0),
    1103: ("selenium_ug",    1.0),
    1096: ("chromium_mg",    0.001),   # µg → mg
    1101: ("manganese_mg",   1.0),
    1102: ("molybdenum_mg",  0.001),   # µg → mg
    1095: ("zinc_mg",        1.0),
    1106: ("vita_ug",        1.0),     # Vitamin A RAE
    1109: ("vite_mg",        1.0),
    1111: ("vitd2_ug",       1.0),
    1112: ("vitd3_ug",       1.0),
    1185: ("vitk1_ug",       1.0),     # Phylloquinone (K1)
    1183: ("vitk2_ug",       1.0),     # Menaquinone-4 (K2)
    1177: ("folate_ug",      1.0),
    1165: ("vitb1_mg",       1.0),
    1166: ("vitb2_mg",       1.0),
    1167: ("vitb3_mg",       1.0),
    1170: ("vitb5_mg",       1.0),
    1175: ("vitb6_mg",       1.0),
    1176: ("vitb7_ug",       1.0),
    1186: ("vitb9_ug",       1.0),     # Folic acid
    1162: ("vitc_mg",        1.0),
}

_CAROTENOID_IDS: frozenset[int] = frozenset({1107, 1108, 1122, 1123})
_ALL_NUTRIENT_IDS: frozenset[int] = frozenset(_NUTRIENT_MAP) | _CAROTENOID_IDS


class USDAAdapter(FoodDataAdapter):

    def __init__(
        self,
        foods_df:          pd.DataFrame,
        food_nutrients_df: pd.DataFrame,
        food_portions_df:  pd.DataFrame,
        measure_units_df:  pd.DataFrame,
    ) -> None:
        self._foods          = foods_df
        self._food_nutrients = food_nutrients_df
        self._food_portions  = food_portions_df
        self._measure_units  = measure_units_df

        self._cached_items:    Optional[list[FoodItemRecord]]    = None
        self._cached_portions: Optional[list[FoodPortionRecord]] = None
        # fdc_id (str) → generated UUID — populated during _transform()
        self._id_map: dict[str, str] = {}

    # ── public interface ───────────────────────────────────────────────────────

    def adapt_food_items(self) -> list[FoodItemRecord]:
        if self._cached_items is None:
            self._transform()
        return self._cached_items  # type: ignore[return-value]

    def adapt_portions(self) -> list[FoodPortionRecord]:
        if self._cached_items is None:
            self._transform()
        return self._cached_portions  # type: ignore[return-value]

    # ── internal ───────────────────────────────────────────────────────────────

    def _transform(self) -> None:
        self._cached_items    = self._build_food_items()
        self._cached_portions = self._build_portions()

    def _build_food_items(self) -> list[FoodItemRecord]:
        fn = self._food_nutrients[
            self._food_nutrients["nutrient_id"].isin(_ALL_NUTRIENT_IDS)
        ].copy()

        # carotenoids: sum the four pigment nutrient amounts per food
        carot = (
            fn[fn["nutrient_id"].isin(_CAROTENOID_IDS)]
            .groupby("fdc_id")["amount"]
            .sum()
            .reset_index()
            .rename(columns={"amount": "carotenoids_ug"})
        )

        # pivot remaining nutrients from long → wide
        wide = (
            fn[fn["nutrient_id"].isin(_NUTRIENT_MAP)]
            .pivot_table(index="fdc_id", columns="nutrient_id", values="amount", aggfunc="first")
            .reset_index()
        )
        wide.columns = [str(c) for c in wide.columns]

        # rename integer column headers → nutrient field names and apply multipliers
        col_rename = {str(nid): col for nid, (col, _) in _NUTRIENT_MAP.items()}
        wide = wide.rename(columns=col_rename)
        for nid, (col, mult) in _NUTRIENT_MAP.items():
            if mult != 1.0 and col in wide.columns:
                wide[col] *= mult

        # join foods ← wide nutrients ← carotenoids
        df = self._foods.merge(wide, on="fdc_id", how="left")
        df = df.merge(carot, on="fdc_id", how="left")

        df["energy_kj"]   = df["energy_kcal"] * 4.184
        df["freesugar_g"] = None
        df["id"]          = [str(uuid.uuid4()) for _ in range(len(df))]
        df["source"]      = "usda"
        df["external_id"] = df["fdc_id"].astype(str)
        df["is_verified"] = True
        df["created_by"]  = None

        # record the fdc_id → UUID map for use by _build_portions()
        self._id_map = dict(zip(df["external_id"], df["id"]))

        df = df.rename(columns={"description": "name"})

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

    def _build_portions(self) -> list[FoodPortionRecord]:
        fp = self._food_portions.copy()
        fp = fp[fp["gram_weight"].notna() & (fp["gram_weight"] > 0)].copy()

        units = self._measure_units.rename(columns={"id": "measure_unit_id", "name": "unit_name"})
        fp = fp.merge(units, on="measure_unit_id", how="left")

        fp["food_item_id"] = fp["fdc_id"].astype(str).map(self._id_map)
        fp = fp[fp["food_item_id"].notna()].copy()

        fp["description"] = fp.apply(self._portion_description, axis=1)
        fp["id"]          = [str(uuid.uuid4()) for _ in range(len(fp))]

        return [
            FoodPortionRecord(
                id=row["id"],
                food_item_id=row["food_item_id"],
                description=row["description"],
                gram_weight=float(row["gram_weight"]),
            )
            for row in fp.to_dict("records")
        ]

    @staticmethod
    def _portion_description(row: pd.Series) -> str:
        desc = row.get("portion_description")
        if pd.notna(desc) and str(desc).strip():
            return str(desc).strip()
        amt    = row["amount"]   if pd.notna(row.get("amount"))    else ""
        mod    = row["modifier"] if pd.notna(row.get("modifier"))  else ""
        unit   = row.get("unit_name", "")
        suffix = str(mod).strip() or (str(unit).strip() if pd.notna(unit) else "")
        return f"{amt} {suffix}".strip()

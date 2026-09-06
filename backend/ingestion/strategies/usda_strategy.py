"""
USDA SR Legacy ingestion strategy.

Loads five CSV files, filters to the SR Legacy subset, then delegates all
transformation logic to USDAAdapter.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Connection

from ..adapters.usda_adapter import USDAAdapter
from ..base import IngestionStrategy


class USDAIngestionStrategy(IngestionStrategy):
    source = "usda"

    def __init__(self, data_dir: Path) -> None:
        self._usda_dir = data_dir / "USDA-raw-data"

    def ingest(self, conn: Connection) -> None:
        self._clear_existing(conn)

        sr_ids = self._load_sr_legacy_ids()
        foods  = self._load_foods(sr_ids)
        fn     = self._load_food_nutrients(sr_ids)
        fp_raw = self._load_food_portions(sr_ids)
        units  = self._load_measure_units()

        adapter  = USDAAdapter(foods, fn, fp_raw, units)
        items    = adapter.adapt_food_items()
        portions = adapter.adapt_portions()

        self._insert_food_items(conn, items)
        self._insert_food_portions(conn, portions)
        print(f"  [{self.source}] {len(items)} food items, {len(portions)} portions inserted")

    # ── loaders ────────────────────────────────────────────────────────────────

    def _load_sr_legacy_ids(self) -> set[int]:
        df = pd.read_csv(self._usda_dir / "sr_legacy_food.csv", usecols=["fdc_id"])
        return set(df["fdc_id"].astype(int))

    def _load_foods(self, sr_ids: set[int]) -> pd.DataFrame:
        foods = pd.read_csv(
            self._usda_dir / "food.csv",
            usecols=["fdc_id", "description", "food_category_id"],
        )
        foods["fdc_id"] = foods["fdc_id"].astype(int)
        foods = foods[foods["fdc_id"].isin(sr_ids)].copy()

        cats = pd.read_csv(
            self._usda_dir / "food_category.csv",
            usecols=["id", "description"],
        ).rename(columns={"id": "food_category_id", "description": "category"})

        foods = foods.merge(cats, on="food_category_id", how="left")
        return foods.drop(columns=["food_category_id"])

    def _load_food_nutrients(self, sr_ids: set[int]) -> pd.DataFrame:
        df = pd.read_csv(
            self._usda_dir / "food_nutrient.csv",
            usecols=["fdc_id", "nutrient_id", "amount"],
            dtype={"fdc_id": int, "nutrient_id": int, "amount": float},
        )
        return df[df["fdc_id"].isin(sr_ids)].copy()

    def _load_food_portions(self, sr_ids: set[int]) -> pd.DataFrame:
        df = pd.read_csv(
            self._usda_dir / "food_portion.csv",
            usecols=["fdc_id", "amount", "measure_unit_id",
                     "portion_description", "modifier", "gram_weight"],
            dtype={"fdc_id": int},
        )
        return df[df["fdc_id"].isin(sr_ids)].copy()

    def _load_measure_units(self) -> pd.DataFrame:
        return pd.read_csv(self._usda_dir / "measure_unit.csv", usecols=["id", "name"])

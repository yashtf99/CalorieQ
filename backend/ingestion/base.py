"""
Abstract base classes for the ingestion pipeline.

Adapter  — converts raw source DataFrames into normalised records (no I/O)
Strategy — owns the full read → adapt → write lifecycle for one data source
"""
from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd
from sqlalchemy import Connection, text

from .records import FoodItemRecord, FoodPortionRecord


# ── Adapter ────────────────────────────────────────────────────────────────────

class FoodDataAdapter(ABC):
    """
    Transforms raw source DataFrames into normalised FoodItemRecords.
    Receives data already loaded and filtered by the Strategy; does no I/O.
    """

    @abstractmethod
    def adapt_food_items(self) -> list[FoodItemRecord]:
        """Return one FoodItemRecord per row in the source dataset."""
        ...

    def adapt_portions(self) -> list[FoodPortionRecord]:
        """Return portion records. Sources without portion data return []."""
        return []


# ── Strategy ───────────────────────────────────────────────────────────────────

class IngestionStrategy(ABC):
    """
    Encapsulates the full read → adapt → write pipeline for one data source.
    Each concrete strategy handles exactly one source value ('indb', 'usda', …).
    """

    source: ClassVar[str]

    @abstractmethod
    def ingest(self, conn: Connection) -> None:
        """Run the full ingestion inside the provided transaction."""
        ...

    # ── shared helpers ─────────────────────────────────────────────────────────

    def _clear_existing(self, conn: Connection) -> None:
        """
        Delete all seeded rows for this source.
        Portions are deleted explicitly first — belt-and-suspenders against
        environments where SQLite FK enforcement isn't active.
        user_meal_logs.food_item_id becomes NULL via ON DELETE SET NULL.
        """
        conn.execute(text(
            "DELETE FROM food_portions WHERE food_item_id IN "
            "(SELECT id FROM food_items WHERE source = :s)"
        ), {"s": self.source})
        result = conn.execute(
            text("DELETE FROM food_items WHERE source = :s"),
            {"s": self.source},
        )
        print(f"  Cleared {result.rowcount} existing '{self.source}' rows")

    def _insert_food_items(self, conn: Connection, items: list[FoodItemRecord]) -> None:
        if not items:
            return
        rows = [dataclasses.asdict(item) for item in items]
        keys = list(rows[0].keys())
        cols = ", ".join(keys)
        placeholders = ", ".join(f":{k}" for k in keys)
        stmt = text(f"INSERT INTO food_items ({cols}) VALUES ({placeholders})")
        # executemany via list-of-dicts
        conn.execute(stmt, rows)

    def _insert_food_portions(self, conn: Connection, portions: list[FoodPortionRecord]) -> None:
        if not portions:
            return
        rows = [dataclasses.asdict(p) for p in portions]
        stmt = text(
            "INSERT INTO food_portions (id, food_item_id, description, gram_weight) "
            "VALUES (:id, :food_item_id, :description, :gram_weight)"
        )
        conn.execute(stmt, rows)


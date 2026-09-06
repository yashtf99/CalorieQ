"""INDB ingestion strategy — reads INDB-processed/indb.csv, delegates to INDBAdapter."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Connection

from ..adapters.indb_adapter import INDBAdapter
from ..base import IngestionStrategy


class INDBIngestionStrategy(IngestionStrategy):
    source = "indb"

    def __init__(self, data_dir: Path) -> None:
        self._indb_csv = data_dir / "INDB-processed" / "indb.csv"

    def ingest(self, conn: Connection) -> None:
        self._clear_existing(conn)

        df = pd.read_csv(self._indb_csv)
        adapter = INDBAdapter(df)

        items = adapter.adapt_food_items()
        self._insert_food_items(conn, items)
        # INDB has no gram-weight portion data → no food_portions rows
        print(f"  [{self.source}] {len(items)} food items inserted")

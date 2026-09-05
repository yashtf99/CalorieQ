"""
ingest.py — Seed runner
-----------------------
Runs every registered IngestionStrategy in order, each in its own transaction.
Safe to re-run: each strategy clears its own source rows before inserting.

Usage:
    python ingest.py   (run from backend/)

Prerequisites:
    1. Schema created        →  python db/create_db.py
    2. INDB CSVs processed   →  python data/process_raw_data.py
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event

from config import settings
from ingestion.base import IngestionStrategy
from ingestion.strategies.indb_strategy import INDBIngestionStrategy
from ingestion.strategies.usda_strategy import USDAIngestionStrategy

DATA_DIR = Path(__file__).parent / "data"

# ── register strategies in ingestion order ─────────────────────────────────────
STRATEGIES: list[IngestionStrategy] = [
    INDBIngestionStrategy(DATA_DIR),
    USDAIngestionStrategy(DATA_DIR),
]


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)

    if settings.DATABASE_URL.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute("PRAGMA journal_mode = WAL")
            cur.close()

    for strategy in STRATEGIES:
        print(f"\n[{strategy.source.upper()}] Starting ...")
        with engine.begin() as conn:   # commits on exit, rolls back on exception
            strategy.ingest(conn)
        print(f"[{strategy.source.upper()}] Committed.")

    print("\nAll datasets ingested successfully.")


if __name__ == "__main__":
    main()

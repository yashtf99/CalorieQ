"""
create_db.py — Programmatic schema creation
Run: python db/create_db.py [--drop]

Patterns
--------
Singleton  : DatabaseEngine  — one shared SQLAlchemy engine per process
Builder    : SchemaBuilder   — accumulates table/index definitions, materialises in one call
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings  # noqa: E402

from sqlalchemy import (
    Boolean, CHAR, Column, Date, DateTime, Enum,
    ForeignKey, Index, MetaData, Numeric, Table, Text, VARCHAR,
    Engine, create_engine, text,
)



# ── Singleton ──────────────────────────────────────────────────────────────────

class DatabaseEngine:
    """Single shared SQLAlchemy engine. Re-entrant: calling initialise() twice is a no-op."""

    _instance: Optional[DatabaseEngine] = None
    _engine:   Optional[Engine]         = None

    def __new__(cls) -> DatabaseEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialise(self, url: str, **kwargs) -> None:
        if self._engine is None:
            self._engine = create_engine(url, **kwargs)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise RuntimeError("Call DatabaseEngine().initialise(url) first")
        return self._engine


# ── Builder ────────────────────────────────────────────────────────────────────

class SchemaBuilder:
    """
    Builds the complete CalorieQ schema via SQLAlchemy Core.

    Usage:
        SchemaBuilder().create(engine)              # idempotent, safe to re-run
        SchemaBuilder().create(engine, drop=True)   # tear-down + recreate (dev only)
    """

    def __init__(self) -> None:
        self._meta = MetaData()
        self._build()

    # ── private ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        """Define all tables and indexes in FK dependency order."""
        m = self._meta

        # helpers
        _ts  = lambda: Column("created_at", DateTime, nullable=False,
                               server_default=text("CURRENT_TIMESTAMP"))
        _upd = lambda: Column("updated_at", DateTime, nullable=False,
                               server_default=text("CURRENT_TIMESTAMP"))
        _pk  = lambda: Column("id", CHAR(36), primary_key=True)
        _uid = lambda ref, **kw: Column("user_id", CHAR(36),
                                        ForeignKey(ref, ondelete="CASCADE"), nullable=False, **kw)

        # ── users ──────────────────────────────────────────────────────────────
        users = Table("users", m,
            _pk(),
            Column("email",         VARCHAR(255), nullable=False, unique=True),
            Column("password_hash", Text,         nullable=False),
            Column("display_name",  VARCHAR(255)),
            _ts(), _upd(),
        )

        # ── user_profiles ──────────────────────────────────────────────────────
        Table("user_profiles", m,
            Column("user_id",        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"),
                   primary_key=True),
            Column("dob",            Date),
            Column("gender",         VARCHAR(50)),
            Column("height_cm",      Numeric(5, 2)),
            Column("activity_level", VARCHAR(50)),
            _upd(),
        )

        # ── goals ──────────────────────────────────────────────────────────────
        goals = Table("goals", m,
            _pk(),
            _uid("users.id"),
            Column("goal_type",        Enum("lose", "maintain", "gain"), nullable=False),
            Column("daily_calories",   Numeric(7, 2)),
            Column("protein_g",        Numeric(6, 2)),
            Column("carbs_g",          Numeric(6, 2)),
            Column("fat_g",            Numeric(6, 2)),
            Column("fibre_g",          Numeric(6, 2)),
            Column("weight_target_kg", Numeric(5, 2)),
            Column("active_from",      DateTime, nullable=False),
            Column("active_to",        DateTime),
            _ts(),
        )
        Index("idx_goals_user_active", goals.c.user_id, goals.c.active_to)

        # ── food_items ─────────────────────────────────────────────────────────
        food_items = Table("food_items", m,
            _pk(),
            Column("source",         VARCHAR(20),  nullable=False),
            Column("external_id",    VARCHAR(50)),
            Column("name",           VARCHAR(500), nullable=False),
            Column("category",       VARCHAR(255)),
            Column("energy_kcal",    Numeric(7, 2)),
            Column("energy_kj",      Numeric(7, 2)),
            Column("protein_g",      Numeric(6, 2)),
            Column("carb_g",         Numeric(6, 2)),
            Column("fat_g",          Numeric(6, 2)),
            Column("freesugar_g",    Numeric(6, 2)),
            Column("fibre_g",        Numeric(6, 2)),
            Column("sfa_g",          Numeric(6, 2)),
            Column("mufa_g",         Numeric(6, 2)),
            Column("pufa_g",         Numeric(6, 2)),
            Column("cholesterol_mg", Numeric(7, 2)),
            Column("calcium_mg",     Numeric(7, 2)),
            Column("phosphorus_mg",  Numeric(7, 2)),
            Column("magnesium_mg",   Numeric(7, 2)),
            Column("sodium_mg",      Numeric(7, 2)),
            Column("potassium_mg",   Numeric(7, 2)),
            Column("iron_mg",        Numeric(7, 4)),
            Column("copper_mg",      Numeric(7, 4)),
            Column("selenium_ug",    Numeric(7, 4)),
            Column("chromium_mg",    Numeric(7, 4)),
            Column("manganese_mg",   Numeric(7, 4)),
            Column("molybdenum_mg",  Numeric(7, 4)),
            Column("zinc_mg",        Numeric(7, 4)),
            Column("vita_ug",        Numeric(7, 2)),
            Column("vite_mg",        Numeric(7, 4)),
            Column("vitd2_ug",       Numeric(7, 4)),
            Column("vitd3_ug",       Numeric(7, 4)),
            Column("vitk1_ug",       Numeric(7, 4)),
            Column("vitk2_ug",       Numeric(7, 4)),
            Column("folate_ug",      Numeric(7, 2)),
            Column("vitb1_mg",       Numeric(7, 4)),
            Column("vitb2_mg",       Numeric(7, 4)),
            Column("vitb3_mg",       Numeric(7, 4)),
            Column("vitb5_mg",       Numeric(7, 4)),
            Column("vitb6_mg",       Numeric(7, 4)),
            Column("vitb7_ug",       Numeric(7, 4)),
            Column("vitb9_ug",       Numeric(7, 4)),
            Column("vitc_mg",        Numeric(7, 2)),
            Column("carotenoids_ug", Numeric(7, 2)),
            Column("is_verified",    Boolean,      nullable=False, server_default=text("1")),
            Column("created_by",     CHAR(36),     ForeignKey("users.id", ondelete="SET NULL")),
            _ts(),
        )
        Index("idx_food_source", food_items.c.source)
        Index("idx_food_name",   food_items.c.name)

        # ── food_portions ──────────────────────────────────────────────────────
        Table("food_portions", m,
            _pk(),
            Column("food_item_id", CHAR(36), ForeignKey("food_items.id", ondelete="CASCADE"),
                   nullable=False),
            Column("description",  VARCHAR(255), nullable=False),
            Column("gram_weight",  Numeric(7, 2), nullable=False),
            _ts(),
        )

        # ── user_meal_logs ─────────────────────────────────────────────────────
        meal_logs = Table("user_meal_logs", m,
            _pk(),
            _uid("users.id"),
            Column("food_item_id",       CHAR(36), ForeignKey("food_items.id", ondelete="SET NULL")),
            Column("logged_at",          DateTime, nullable=False),
            Column("meal_type",          VARCHAR(20),  nullable=False),
            Column("food_name_snapshot", VARCHAR(500), nullable=False),
            Column("quantity_g",         Numeric(7, 2), nullable=False),
            Column("energy_kcal",        Numeric(7, 2), nullable=False),
            Column("protein_g",          Numeric(6, 2), nullable=False),
            Column("carb_g",             Numeric(6, 2), nullable=False),
            Column("fat_g",              Numeric(6, 2), nullable=False),
            Column("fibre_g",            Numeric(6, 2)),
            Column("sodium_mg",          Numeric(7, 2)),
            Column("source",             VARCHAR(10), nullable=False),
            Column("notes",              Text),
            _ts(),
        )
        Index("idx_logs_user_date", meal_logs.c.user_id, meal_logs.c.logged_at)
        Index("idx_logs_meal_type", meal_logs.c.meal_type)

        # ── weight_logs ────────────────────────────────────────────────────────
        weight_logs = Table("weight_logs", m,
            _pk(),
            _uid("users.id"),
            Column("weight_kg", Numeric(5, 2), nullable=False),
            Column("logged_at", DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
            Column("notes",     Text),
        )
        Index("idx_weight_user_date", weight_logs.c.user_id, weight_logs.c.logged_at)

        # ── chat_sessions ──────────────────────────────────────────────────────
        chat_sessions = Table("chat_sessions", m,
            _pk(),
            _uid("users.id"),
            Column("title", VARCHAR(500)),
            _ts(), _upd(),
        )
        Index("idx_sessions_user", chat_sessions.c.user_id)

        # ── chat_messages ──────────────────────────────────────────────────────
        chat_messages = Table("chat_messages", m,
            _pk(),
            Column("session_id",    CHAR(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                   nullable=False),
            _uid("users.id"),
            Column("user_query",    Text, nullable=False),
            Column("chat_response", Text, nullable=False),
            _ts(),
        )
        Index("idx_messages_session", chat_messages.c.session_id)

        # ── refresh_tokens ─────────────────────────────────────────────────────
        refresh_tokens = Table("refresh_tokens", m,
            _pk(),
            _uid("users.id"),
            Column("token_hash", CHAR(64),  nullable=False, unique=True),
            Column("expires_at", DateTime,  nullable=False),
            Column("revoked",    Boolean,   nullable=False, server_default=text("0")),
            _ts(),
        )
        Index("idx_refresh_tokens_user", refresh_tokens.c.user_id)

    # ── public ─────────────────────────────────────────────────────────────────

    def create(self, engine: Engine, *, drop: bool = False) -> None:
        if drop:
            self._meta.drop_all(engine)
            print("  Dropped all existing tables")
        self._meta.create_all(engine, checkfirst=True)
        print(f"  Created / verified {len(self._meta.tables)} tables: "
              f"{', '.join(sorted(self._meta.tables))}")


# ── entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Create CalorieQ database schema")
    parser.add_argument("--drop", action="store_true",
                        help="Drop all tables before recreating (dev/reset only)")
    args = parser.parse_args()

    db = DatabaseEngine()
    db.initialise(settings.DATABASE_URL, pool_pre_ping=True)

    print(f"{'Dropping + recreating' if args.drop else 'Creating'} schema ...")
    SchemaBuilder().create(db.engine, drop=args.drop)
    print("Done.")


if __name__ == "__main__":
    main()

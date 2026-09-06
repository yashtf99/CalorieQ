from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def _apply_sqlite_pragmas(dbapi_conn, _) -> None:
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.close()


class DatabasePool:
    """
    Singleton — one engine and session factory for the entire process lifetime.
    SQLAlchemy's connection pool is managed by the engine; this class ensures
    the engine is never created more than once.
    """

    _instance: Optional["DatabasePool"] = None

    def __new__(cls) -> "DatabasePool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self) -> None:
        is_sqlite = settings.DATABASE_URL.startswith("sqlite")

        self._engine: Engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if is_sqlite else {},
        )

        if is_sqlite:
            event.listen(self._engine, "connect", _apply_sqlite_pragmas)

        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def new_session(self) -> Session:
        return self._session_factory()


# Process-wide singleton — imported everywhere sessions are needed
db_pool = DatabasePool()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session, always closes on exit."""
    db = db_pool.new_session()
    try:
        yield db
    finally:
        db.close()

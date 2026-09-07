import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so Base.metadata knows about them before create_all
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.chat_session import ChatSession  # noqa: F401
from app.models.food_item import FoodItem  # noqa: F401
from app.models.food_portion import FoodPortion  # noqa: F401
from app.models.goal import Goal  # noqa: F401
from app.models.meal_log import MealLog  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.weight_log import WeightLog  # noqa: F401
from app.orm.base import Base
from app.orm.session import get_db
from app.main import app


def _apply_pragmas(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.close()


@pytest.fixture
def engine():
    """Fresh in-memory SQLite DB per test — full isolation."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(eng, "connect", _apply_pragmas)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def token_headers(client):
    """Register a user and return auth headers. Reuses the same client fixture DB."""
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "fixture@test.com", "password": "password123", "display_name": "Fixture User"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    """TestClient with get_db overridden to use the test session."""
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()

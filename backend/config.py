import warnings
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).parent
_DEFAULT_DB_URL = f"sqlite:///{_HERE / 'db' / 'calorieq.db'}"
_DEV_SECRET = "dev-secret-change-before-deploy"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Absolute path — works regardless of cwd when the app starts
        env_file=str(_HERE / ".env"),
        frozen=True,
        extra="ignore",
    )

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = _DEFAULT_DB_URL

    # ── Auth ───────────────────────────────────────────────────────────────────
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── AWS / Bedrock ──────────────────────────────────────────────────────────
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "global.amazon.nova-2-lite-v1:0"

    # ── Chat ───────────────────────────────────────────────────────────────────
    CHAT_SESSION_TIMEOUT_MINUTES: int = 20  # Reuse session within this window

    # ── Secrets (set in .env) ──────────────────────────────────────────────────
    SECRET_KEY: str = _DEV_SECRET
    AWS_BEARER_TOKEN_BEDROCK: str = ""


settings = Settings()

if settings.SECRET_KEY == _DEV_SECRET:
    warnings.warn(
        "SECRET_KEY is using the dev default — set a strong random value in .env before deploying.",
        stacklevel=1,
    )

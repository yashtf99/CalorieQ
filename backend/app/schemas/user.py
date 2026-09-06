from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ActivityLevel = Literal["sedentary", "lightly_active", "active", "very_active"]


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class UserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)


class RegisterResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ── Profile ───────────────────────────────────────────────────────────────────

class UserProfileIn(BaseModel):
    """All fields optional — supports partial PATCH semantics."""
    dob: date | None = None
    gender: Literal["male", "female", "other", "prefer_not_to_say"] | None = None
    height_cm: float | None = Field(default=None, gt=50, lt=300)
    activity_level: ActivityLevel | None = None
    # Providing current_weight_kg creates a weight_log entry; it is not stored on the profile row.
    current_weight_kg: float | None = Field(default=None, gt=20, lt=700)


class UserProfileOut(BaseModel):
    """current_weight_kg is derived from the latest weight_logs row, not the profile table."""
    dob: date | None
    gender: str | None
    height_cm: float | None
    activity_level: str | None
    current_weight_kg: float | None
    updated_at: datetime | None  # None when profile has never been set

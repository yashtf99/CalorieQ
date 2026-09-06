from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.constraints import (
    PROFILE_HEIGHT_GT, PROFILE_HEIGHT_LT,
    PROFILE_WEIGHT_GT, PROFILE_WEIGHT_LT,
)

ActivityLevel = Literal["sedentary", "lightly_active", "active", "very_active"]


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


class UserProfileIn(BaseModel):
    """All fields optional — supports partial PATCH semantics."""
    dob: date | None = None
    gender: Literal["male", "female", "other", "prefer_not_to_say"] | None = None
    height_cm: float | None = Field(default=None, gt=PROFILE_HEIGHT_GT, lt=PROFILE_HEIGHT_LT)
    activity_level: ActivityLevel | None = None
    current_weight_kg: float | None = Field(default=None, gt=PROFILE_WEIGHT_GT, lt=PROFILE_WEIGHT_LT)


class UserProfileOut(BaseModel):
    """current_weight_kg is derived from the latest weight_logs row, not the profile table."""
    dob: date | None
    gender: str | None
    height_cm: float | None
    activity_level: str | None
    current_weight_kg: float | None
    updated_at: datetime | None

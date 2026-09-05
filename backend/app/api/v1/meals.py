from datetime import datetime, time, timedelta, timezone

import pytz
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import UnprocessableError
from app.models.user import User
from app.orm.session import get_db
from app.schemas.common import PaginatedResponse, make_paginated
from app.schemas.meal_log import MealLogIn, MealLogOut, MealLogPatchIn
from app.services import meal_log_service

router = APIRouter(prefix="/meals", tags=["meals"])


def _parse_bound(value: str, user_tz, is_end_date_only: bool = False) -> datetime:
    """
    Parse a date or datetime string into a tz-aware datetime.

    Accepted formats:
      - YYYY-MM-DD            → treated as midnight in user_tz
                                (if is_end_date_only, extended to next midnight so the
                                 whole day is included in a half-open [start, end) range)
      - YYYY-MM-DDTHH:MM:SS   → naive, treated as user_tz
      - YYYY-MM-DDTHH:MM      → naive, treated as user_tz
      - YYYY-MM-DDTHH:MM:SS±HH:MM  → explicit offset, used directly
    """
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise UnprocessableError(
            f"Cannot parse '{value}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
        )

    is_date_only = "T" not in value and " " not in value

    if dt.tzinfo is None:
        dt = user_tz.localize(dt)

    if is_date_only and is_end_date_only:
        dt = dt + timedelta(days=1)

    return dt


def _resolve_date_range(
    date: str | None,
    start: str | None,
    end: str | None,
    tz: str,
) -> tuple[datetime, datetime]:
    """Return UTC-aware (start_inclusive, end_exclusive) bounds."""
    if date and (start or end):
        raise UnprocessableError("Use either date or start/end — not both")
    if (start and not end) or (end and not start):
        raise UnprocessableError("start and end must both be provided")

    try:
        user_tz = pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        raise UnprocessableError(f"Unknown timezone: {tz}")

    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise UnprocessableError("date must be YYYY-MM-DD")
        start_local = user_tz.localize(datetime.combine(day, time.min))
        end_local = start_local + timedelta(days=1)

    elif start and end:
        start_local = _parse_bound(start, user_tz, is_end_date_only=False)
        end_local = _parse_bound(end, user_tz, is_end_date_only=True)
        if end_local <= start_local:
            raise UnprocessableError("end must be after start")

    else:
        today = datetime.now(user_tz).date()
        start_local = user_tz.localize(datetime.combine(today, time.min))
        end_local = start_local + timedelta(days=1)

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


@router.post("", response_model=MealLogOut, status_code=201)
def create_meal(
    req: MealLogIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_log_service.create_meal_log(db, current_user.id, req)


@router.get("", response_model=PaginatedResponse[MealLogOut])
def list_meals(
    date: str | None = Query(default=None, description="YYYY-MM-DD — whole day shortcut"),
    start: str | None = Query(default=None, description="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (range start, inclusive)"),
    end: str | None = Query(default=None, description="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (range end — date inclusive, datetime exclusive)"),
    tz: str = Query(default="UTC", description="IANA timezone e.g. Asia/Kolkata"),
    meal_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_start, date_end = _resolve_date_range(date, start, end, tz)
    logs, total = meal_log_service.list_meal_logs(
        db, current_user.id, date_start, date_end, meal_type, page, page_size
    )
    return make_paginated(
        [MealLogOut.model_validate(l) for l in logs], total, page, page_size
    )


@router.get("/{log_id}", response_model=MealLogOut)
def get_meal(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_log_service.get_meal_log(db, current_user.id, log_id)


@router.patch("/{log_id}", response_model=MealLogOut)
def update_meal(
    log_id: str,
    req: MealLogPatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_log_service.update_meal_log(db, current_user.id, log_id, req)


@router.delete("/{log_id}", status_code=204)
def delete_meal(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal_log_service.delete_meal_log(db, current_user.id, log_id)

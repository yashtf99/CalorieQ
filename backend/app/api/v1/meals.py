from datetime import datetime, time, timedelta, timezone

import pytz
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import UnprocessableError
from app.models.user import User
from app.orm.session import get_db
from app.schemas.common import PaginatedResponse, make_paginated
from app.schemas.meal_log import MealLogIn, MealLogOut, MealLogPatchIn
from app.schemas.params import MealListParams
from app.services import meal_log_service

router = APIRouter(prefix="/meals", tags=["meals"])


def _parse_bound(value: str, user_tz, is_end_date_only: bool = False) -> datetime:
    """
    YYYY-MM-DD            → midnight in user_tz (end extends +1 day for inclusive range)
    YYYY-MM-DDTHH:MM:SS   → naive, localised to user_tz
    YYYY-MM-DDTHH:MM:SS±HH:MM → explicit offset used directly
    """
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise UnprocessableError(f"Cannot parse '{value}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")

    is_date_only = "T" not in value and " " not in value
    if dt.tzinfo is None:
        dt = user_tz.localize(dt)
    if is_date_only and is_end_date_only:
        dt = dt + timedelta(days=1)
    return dt


def resolve_meal_date_range(params: MealListParams) -> tuple[datetime, datetime]:
    """Convert validated MealListParams into naive-UTC (start, end) bounds."""
    user_tz = pytz.timezone(params.tz)

    if params.date:
        day = datetime.strptime(params.date, "%Y-%m-%d").date()
        start_local = user_tz.localize(datetime.combine(day, time.min))
        end_local = start_local + timedelta(days=1)
    elif params.start and params.end:
        start_local = _parse_bound(params.start, user_tz, is_end_date_only=False)
        end_local = _parse_bound(params.end, user_tz, is_end_date_only=True)
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
    meal = meal_log_service.create_meal_log(db, current_user.id, req)
    db.commit()
    return meal


@router.get("/history", response_model=PaginatedResponse[MealLogOut])
def list_meals(
    params: MealListParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_start, date_end = resolve_meal_date_range(params)
    logs, total = meal_log_service.list_meal_logs(
        db, current_user.id, date_start, date_end, params.meal_type, params.page, params.page_size
    )
    return make_paginated(
        [MealLogOut.model_validate(l) for l in logs], total, page=params.page, page_size=params.page_size
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
    meal = meal_log_service.update_meal_log(db, current_user.id, log_id, req)
    db.commit()
    return meal


@router.delete("/{log_id}", status_code=204)
def delete_meal(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal_log_service.delete_meal_log(db, current_user.id, log_id)
    db.commit()

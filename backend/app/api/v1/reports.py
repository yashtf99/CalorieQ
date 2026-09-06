from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.user import User
from app.orm.session import get_db
from app.schemas.report import DailySummaryOut, MicrosReportOut, WeeklyReportOut
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

_WEEK_OF_DESC  = "Any date in the target week (YYYY-MM-DD) — snaps to Sun-Sat week"
_START_DESC    = "Range start YYYY-MM-DD (use with end=)"
_END_DESC      = "Range end YYYY-MM-DD inclusive (use with start=)"
_TZ_DESC       = "IANA timezone e.g. Asia/Kolkata (default UTC)"


@router.get("/daily_summary", response_model=DailySummaryOut)
def daily_summary(
    date: str | None = Query(default=None, description="YYYY-MM-DD (default: today)"),
    tz: str = Query(default="UTC", description=_TZ_DESC),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.get_daily_summary(db, current_user.id, date, tz)


@router.get("/weekly", response_model=WeeklyReportOut)
def weekly_report(
    week_of: str | None = Query(default=None, description=_WEEK_OF_DESC),
    start: str | None = Query(default=None, description=_START_DESC),
    end: str | None = Query(default=None, description=_END_DESC),
    tz: str = Query(default="UTC", description=_TZ_DESC),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_d, end_d, user_tz = report_service.resolve_range(week_of, start, end, tz)
    return report_service.get_weekly_report(db, current_user.id, start_d, end_d, user_tz)


@router.get("/micros", response_model=MicrosReportOut)
def micros_report(
    week_of: str | None = Query(default=None, description=_WEEK_OF_DESC),
    start: str | None = Query(default=None, description=_START_DESC),
    end: str | None = Query(default=None, description=_END_DESC),
    tz: str = Query(default="UTC", description=_TZ_DESC),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_d, end_d, user_tz = report_service.resolve_range(week_of, start, end, tz)
    return report_service.get_micros_report(db, current_user.id, start_d, end_d, user_tz)

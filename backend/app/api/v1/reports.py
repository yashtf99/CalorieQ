from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.user import User
from app.orm.session import get_db
from app.schemas.params import DailySummaryParams, ReportRangeParams
from app.schemas.report import DailySummaryOut, MicrosReportOut, WeeklyReportOut
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily_summary", response_model=DailySummaryOut)
def daily_summary(
    params: DailySummaryParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.get_daily_summary(db, current_user.id, params.date, params.tz)


@router.get("/weekly", response_model=WeeklyReportOut)
def weekly_report(
    params: ReportRangeParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_d, end_d, user_tz = report_service.resolve_range(params.week_of, params.start, params.end, params.tz)
    return report_service.get_weekly_report(db, current_user.id, start_d, end_d, user_tz)


@router.get("/micros", response_model=MicrosReportOut)
def micros_report(
    params: ReportRangeParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_d, end_d, user_tz = report_service.resolve_range(params.week_of, params.start, params.end, params.tz)
    return report_service.get_micros_report(db, current_user.id, start_d, end_d, user_tz)

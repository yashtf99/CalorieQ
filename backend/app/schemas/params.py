"""
Query parameter schemas using FastAPI Depends.
All incoming request param validation lives here — format checks, mutual
exclusion, ordering — so services only receive already-validated values.
"""
from dataclasses import dataclass

import pytz
from fastapi import Query
from typing import Annotated

from app.core.exceptions import UnprocessableError


def _require_valid_tz(tz: str) -> str:
    try:
        pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        raise UnprocessableError(f"Unknown timezone: {tz}")
    return tz


def _require_date(value: str, field: str) -> str:
    from datetime import datetime
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise UnprocessableError(f"{field} must be YYYY-MM-DD")
    return value


# ── Meal list params ──────────────────────────────────────────────────────────

@dataclass
class MealListParams:
    date: str | None
    start: str | None
    end: str | None
    tz: str
    meal_type: str | None
    page: int
    page_size: int

    def __init__(
        self,
        date: Annotated[str | None, Query(description="YYYY-MM-DD single day")] = None,
        start: Annotated[str | None, Query(description="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (range start, inclusive)")] = None,
        end: Annotated[str | None, Query(description="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (range end)")] = None,
        tz: Annotated[str, Query(description="IANA timezone e.g. Asia/Kolkata")] = "UTC",
        meal_type: Annotated[str | None, Query()] = None,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    ):
        if date and (start or end):
            raise UnprocessableError("Use either date or start/end — not both")
        if bool(start) != bool(end):
            raise UnprocessableError("start and end must both be provided")

        _require_valid_tz(tz)

        if date:
            _require_date(date, "date")

        self.date = date
        self.start = start
        self.end = end
        self.tz = tz
        self.meal_type = meal_type
        self.page = page
        self.page_size = page_size


# ── Report range params ───────────────────────────────────────────────────────

@dataclass
class ReportRangeParams:
    week_of: str | None
    start: str | None
    end: str | None
    tz: str

    def __init__(
        self,
        week_of: Annotated[str | None, Query(description="Any date in the target week (YYYY-MM-DD) — snaps to Sun-Sat week")] = None,
        start: Annotated[str | None, Query(description="Range start YYYY-MM-DD")] = None,
        end: Annotated[str | None, Query(description="Range end YYYY-MM-DD inclusive")] = None,
        tz: Annotated[str, Query(description="IANA timezone e.g. Asia/Kolkata")] = "UTC",
    ):
        if week_of and (start or end):
            raise UnprocessableError("Use week_of or start/end — not both")
        if bool(start) != bool(end):
            raise UnprocessableError("start and end must both be provided")

        _require_valid_tz(tz)

        if week_of:
            _require_date(week_of, "week_of")
        if start:
            _require_date(start, "start")
        if end:
            _require_date(end, "end")

        if start and end:
            from datetime import datetime
            s = datetime.strptime(start, "%Y-%m-%d").date()
            e = datetime.strptime(end, "%Y-%m-%d").date()
            if e < s:
                raise UnprocessableError("end must be on or after start")

        self.week_of = week_of
        self.start = start
        self.end = end
        self.tz = tz


# ── Daily summary params ──────────────────────────────────────────────────────

@dataclass
class DailySummaryParams:
    date: str | None
    tz: str

    def __init__(
        self,
        date: Annotated[str | None, Query(description="YYYY-MM-DD (default: today)")] = None,
        tz: Annotated[str, Query(description="IANA timezone e.g. Asia/Kolkata")] = "UTC",
    ):
        _require_valid_tz(tz)
        if date:
            _require_date(date, "date")
        self.date = date
        self.tz = tz

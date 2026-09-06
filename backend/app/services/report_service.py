from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

import pytz
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import UnprocessableError
from app.models.food_item import FoodItem
from app.models.goal import Goal
from app.models.meal_log import MealLog
from app.models.weight_log import WeightLog

# ── Constants (change WEEK_START_DAY to 0 for Mon-Sun, 6 for Sun-Sat) ────────
from app.core.constraints import REPORT_MAX_DAYS as MAX_REPORT_DAYS, WEEK_START_DAY

MICRO_COLUMNS: list[str] = [
    "calcium_mg", "phosphorus_mg", "magnesium_mg", "potassium_mg",
    "iron_mg", "copper_mg", "selenium_ug", "chromium_mg",
    "manganese_mg", "molybdenum_mg", "zinc_mg", "cholesterol_mg",
    "vita_ug", "vite_mg", "vitd2_ug", "vitd3_ug",
    "vitk1_ug", "vitk2_ug", "folate_ug",
    "vitb1_mg", "vitb2_mg", "vitb3_mg", "vitb5_mg",
    "vitb6_mg", "vitb7_ug", "vitb9_ug", "vitc_mg",
    "carotenoids_ug",
]


# ── Range helpers ─────────────────────────────────────────────────────────────

def week_bounds(d: date) -> tuple[date, date]:
    """Return the (Sunday, Saturday) of the WEEK_START_DAY-anchored week that contains d."""
    days_since_start = (d.weekday() - WEEK_START_DAY) % 7
    start = d - timedelta(days=days_since_start)
    return start, start + timedelta(days=6)


def resolve_range(
    week_of: str | None,
    start: str | None,
    end: str | None,
    tz_str: str,
) -> tuple[date, date, pytz.BaseTzInfo]:
    """
    Pure domain logic — input format/mutual-exclusion validation is done upstream
    in ReportRangeParams before this is called.
    """
    user_tz = pytz.timezone(tz_str)

    if week_of:
        start_d, end_d = week_bounds(datetime.strptime(week_of, "%Y-%m-%d").date())
    elif start and end:
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        start_d, end_d = week_bounds(datetime.now(user_tz).date())

    if (end_d - start_d).days >= MAX_REPORT_DAYS:
        raise UnprocessableError(f"Range exceeds {MAX_REPORT_DAYS}-day maximum")

    return start_d, end_d, user_tz


# ── Internal date/time utilities ──────────────────────────────────────────────

def _day_utc_bounds(d: date, user_tz) -> tuple[datetime, datetime]:
    """Naive-UTC (start, end) for a single day in user_tz."""
    start_local = user_tz.localize(datetime.combine(d, time.min))
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(timezone.utc).replace(tzinfo=None),
        end_local.astimezone(timezone.utc).replace(tzinfo=None),
    )


def _range_utc(start_d: date, end_d: date, user_tz) -> tuple[datetime, datetime]:
    """Naive-UTC bounds spanning [start_d, end_d] inclusive in user_tz."""
    start_utc, _ = _day_utc_bounds(start_d, user_tz)
    _, end_utc = _day_utc_bounds(end_d, user_tz)
    return start_utc, end_utc


def _group_by_tz_date(
    logs: list[MealLog], user_tz
) -> defaultdict[date, list[MealLog]]:
    groups: defaultdict[date, list[MealLog]] = defaultdict(list)
    for log in logs:
        local_dt = log.logged_at.replace(tzinfo=timezone.utc).astimezone(user_tz)
        groups[local_dt.date()].append(log)
    return groups


def _sum_macros(logs: list[MealLog]) -> dict:
    return {
        "energy_kcal": round(sum(float(l.energy_kcal) for l in logs), 2),
        "protein_g":   round(sum(float(l.protein_g)   for l in logs), 2),
        "carb_g":      round(sum(float(l.carb_g)      for l in logs), 2),
        "fat_g":       round(sum(float(l.fat_g)        for l in logs), 2),
        "fibre_g":     round(sum(float(l.fibre_g or 0) for l in logs), 2),
    }


def _goal_dict(goal: Goal | None) -> dict | None:
    if not goal:
        return None
    return {
        "daily_calories":   float(goal.daily_calories)   if goal.daily_calories   else None,
        "protein_g":        float(goal.protein_g)        if goal.protein_g        else None,
        "carbs_g":          float(goal.carbs_g)          if goal.carbs_g          else None,
        "fat_g":            float(goal.fat_g)            if goal.fat_g            else None,
        "fibre_g":          float(goal.fibre_g)          if goal.fibre_g          else None,
        "weight_target_kg": float(goal.weight_target_kg) if goal.weight_target_kg else None,
    }


# ── Goal lookups ──────────────────────────────────────────────────────────────

def _active_goal(db: Session, user_id: str) -> Goal | None:
    """Goal currently active (active_to IS NULL)."""
    return (
        db.query(Goal)
        .filter(Goal.user_id == user_id, Goal.active_to == None)  # noqa: E711
        .first()
    )


def _goal_for_period(db: Session, user_id: str, start_d: date, end_d: date, user_tz) -> Goal | None:
    """Most recently set goal that started at or before the end of the period."""
    _, end_utc = _range_utc(start_d, end_d, user_tz)
    return (
        db.query(Goal)
        .filter(
            Goal.user_id == user_id,
            Goal.active_from <= end_utc,
        )
        .order_by(Goal.active_from.desc())
        .first()
    )


# ── Report functions ──────────────────────────────────────────────────────────

def get_daily_summary(
    db: Session, user_id: str, date_str: str | None, tz_str: str
) -> dict:
    # Input format validated upstream in DailySummaryParams
    user_tz = pytz.timezone(tz_str)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now(user_tz).date()

    start_utc, end_utc = _day_utc_bounds(target_date, user_tz)

    logs = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.logged_at >= start_utc,
        MealLog.logged_at < end_utc,
    ).all()

    consumed = _sum_macros(logs)
    goal = _active_goal(db, user_id)
    gd = _goal_dict(goal)

    remaining = None
    if goal and gd:
        remaining = {
            "energy_kcal": round(float(goal.daily_calories or 0) - consumed["energy_kcal"], 2) if goal.daily_calories else None,
            "protein_g":   round(float(goal.protein_g or 0)      - consumed["protein_g"],   2) if goal.protein_g    else None,
            "carbs_g":     round(float(goal.carbs_g or 0)         - consumed["carb_g"],      2) if goal.carbs_g      else None,
            "fat_g":       round(float(goal.fat_g or 0)           - consumed["fat_g"],       2) if goal.fat_g        else None,
        }

    return {
        "date": target_date.isoformat(),
        "goal": gd,
        "consumed": consumed,
        "remaining": remaining,
        "meals_tracked": len(logs),
    }


def get_weekly_report(
    db: Session,
    user_id: str,
    start_d: date,
    end_d: date,
    user_tz,
) -> dict:
    start_utc, end_utc = _range_utc(start_d, end_d, user_tz)

    logs = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.logged_at >= start_utc,
        MealLog.logged_at < end_utc,
    ).all()

    groups = _group_by_tz_date(logs, user_tz)

    # Per-day rows — zero-fill days with no logs
    data = []
    current = start_d
    while current <= end_d:
        data.append({"date": current.isoformat(), **_sum_macros(groups.get(current, []))})
        current += timedelta(days=1)

    days_with_logs = sum(1 for row in data if row["energy_kcal"] > 0)

    if days_with_logs > 0:
        period_avg = {
            "energy_kcal": round(sum(r["energy_kcal"] for r in data) / days_with_logs, 2),
            "protein_g":   round(sum(r["protein_g"]   for r in data) / days_with_logs, 2),
            "carb_g":      round(sum(r["carb_g"]      for r in data) / days_with_logs, 2),
            "fat_g":       round(sum(r["fat_g"]        for r in data) / days_with_logs, 2),
            "fibre_g":     round(sum(r["fibre_g"]      for r in data) / days_with_logs, 2),
        }
    else:
        period_avg = {"energy_kcal": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0, "fibre_g": 0.0}

    goal = _goal_for_period(db, user_id, start_d, end_d, user_tz)

    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == user_id,
        WeightLog.logged_at >= start_utc,
        WeightLog.logged_at < end_utc,
    ).order_by(WeightLog.logged_at.asc()).all()

    return {
        "start": start_d.isoformat(),
        "end": end_d.isoformat(),
        "days_with_logs": days_with_logs,
        "goal": _goal_dict(goal),
        "actual_period_avg": period_avg,
        "data": data,
        "weight_logs": [
            {"logged_at": w.logged_at.isoformat(), "weight_kg": float(w.weight_kg)}
            for w in weight_logs
        ],
    }


def get_micros_report(
    db: Session,
    user_id: str,
    start_d: date,
    end_d: date,
    user_tz,
) -> dict:
    start_utc, end_utc = _range_utc(start_d, end_d, user_tz)

    pairs = (
        db.query(MealLog, FoodItem)
        .join(FoodItem, MealLog.food_item_id == FoodItem.id)
        .filter(
            MealLog.user_id == user_id,
            MealLog.logged_at >= start_utc,
            MealLog.logged_at < end_utc,
        )
        .all()
    )

    totals: dict[str, float] = {}
    for log, food in pairs:
        factor = float(log.quantity_g) / 100
        for col in MICRO_COLUMNS:
            val = getattr(food, col)
            if val is not None:
                totals[col] = round(totals.get(col, 0.0) + float(val) * factor, 4)

    return {
        "start": start_d.isoformat(),
        "end": end_d.isoformat(),
        "note": "Free-form entries without a linked food item are excluded — micro data requires a food item reference.",
        "totals": {col: totals.get(col) for col in MICRO_COLUMNS},
    }

from pydantic import BaseModel


class ConsumedTotals(BaseModel):
    energy_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fibre_g: float


class GoalTargets(BaseModel):
    daily_calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fibre_g: float | None
    weight_target_kg: float | None


class RemainingTargets(BaseModel):
    energy_kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None


class DailySummaryOut(BaseModel):
    date: str
    goal: GoalTargets | None
    consumed: ConsumedTotals
    remaining: RemainingTargets | None
    meals_tracked: int


class DailyMacroRow(BaseModel):
    date: str
    energy_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fibre_g: float


class WeightLogPoint(BaseModel):
    logged_at: str
    weight_kg: float


class WeeklyReportOut(BaseModel):
    start: str
    end: str
    days_with_logs: int
    goal: GoalTargets | None
    actual_period_avg: ConsumedTotals
    data: list[DailyMacroRow]
    weight_logs: list[WeightLogPoint]


class MicrosReportOut(BaseModel):
    start: str
    end: str
    note: str
    totals: dict[str, float | None]

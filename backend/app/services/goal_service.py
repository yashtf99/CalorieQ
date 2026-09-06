import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, UnprocessableError
from app.models.goal import Goal
from app.schemas.goal import GoalIn, GoalSuggestionOut, GoalSuggestionParams
from app.services.strategies.bmr import BMRStrategy, DEFAULT_BMR_STRATEGY
from app.services.strategies.macro import MacroStrategy, DEFAULT_MACRO_STRATEGY
from app.utils.rounding import nice_calories


def _age(dob: str) -> int:
    birth = date.fromisoformat(dob)
    today = date.today()
    years = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        years -= 1
    return years


def suggest_goals(
    params: GoalSuggestionParams,
    bmr_strategy: BMRStrategy = DEFAULT_BMR_STRATEGY,
    macro_strategy: MacroStrategy = DEFAULT_MACRO_STRATEGY,
) -> GoalSuggestionOut:
    try:
        parsed_dob = date.fromisoformat(params.dob)
    except ValueError:
        raise UnprocessableError("dob must be a valid date in YYYY-MM-DD format")
    if parsed_dob >= date.today():
        raise UnprocessableError("dob must be in the past")

    age  = _age(params.dob)
    bmr  = nice_calories(bmr_strategy.calculate(params.weight_kg, params.height_cm, age, params.gender))
    tdee = nice_calories(bmr_strategy.tdee(bmr, params.activity_level))

    suggestions = {
        goal_type: macro_strategy.suggest(tdee, params.weight_kg, goal_type)
        for goal_type in ("lose", "maintain", "gain")
    }
    return GoalSuggestionOut(bmr=bmr, tdee=tdee, suggestions=suggestions)


def create_goal(db: Session, user_id: str, req: GoalIn) -> Goal:
    now = datetime.now(timezone.utc)

    active = (
        db.query(Goal)
        .filter(Goal.user_id == user_id, Goal.active_to == None)  # noqa: E711
        .first()
    )
    if active:
        active.active_to = now

    goal = Goal(
        id=str(uuid.uuid4()),
        user_id=user_id,
        goal_type=req.goal_type,
        daily_calories=req.daily_calories,
        protein_g=req.protein_g,
        carbs_g=req.carbs_g,
        fat_g=req.fat_g,
        fibre_g=req.fibre_g,
        weight_target_kg=req.weight_target_kg,
        active_from=now,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_active_goal(db: Session, user_id: str) -> Goal:
    goal = (
        db.query(Goal)
        .filter(Goal.user_id == user_id, Goal.active_to == None)  # noqa: E711
        .first()
    )
    if not goal:
        raise NotFoundError("No active goal found. Set a goal first.")
    return goal


def get_history(db: Session, user_id: str, page: int, page_size: int) -> tuple[list[Goal], int]:
    base = db.query(Goal).filter(Goal.user_id == user_id)
    total = base.with_entities(func.count()).scalar()
    goals = (
        base.order_by(Goal.active_from.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return goals, total

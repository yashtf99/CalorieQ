import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.goal import Goal
from app.schemas.goal import GoalIn


def create_goal(db: Session, user_id: str, req: GoalIn) -> Goal:
    now = datetime.now(timezone.utc)

    # Close the currently active goal, if any
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
    # active_from is set Python-side with microsecond precision — reliable sort key even in tests
    q = db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.active_from.desc())
    total = q.count()
    goals = q.offset((page - 1) * page_size).limit(page_size).all()
    return goals, total

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.user import User
from app.orm.session import get_db
from app.schemas.common import PaginatedResponse, make_paginated
from app.schemas.goal import GoalIn, GoalOut, GoalSuggestionOut, GoalSuggestionParams
from app.services import goal_service

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/suggest", response_model=GoalSuggestionOut)
def suggest_goals(
    params: GoalSuggestionParams = Depends(),
    _: User = Depends(get_current_user),   # auth required — endpoint is per-user context
):
    """
    Returns BMR, TDEE, and suggested macro targets for all three goal types.
    Called during onboarding (step 2 → step 3) and from the Profile page.
    All inputs are explicit query params so this works before profile data is saved.
    """
    return goal_service.suggest_goals(params)


@router.post("", response_model=GoalOut, status_code=201)
def create_goal(
    req: GoalIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return goal_service.create_goal(db, current_user.id, req)


@router.get("/active", response_model=GoalOut)
def get_active_goal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return goal_service.get_active_goal(db, current_user.id)


@router.get("/history", response_model=PaginatedResponse[GoalOut])
def get_goals_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goals, total = goal_service.get_history(db, current_user.id, page, page_size)
    return make_paginated(
        [GoalOut.model_validate(g) for g in goals], total, page, page_size
    )

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constraints import FOOD_SEARCH_PAGE_SIZE_MAX
from app.models.user import User
from app.orm.session import get_db
from app.schemas.common import PaginatedResponse, make_paginated
from app.schemas.food_item import CustomFoodItemIn, FoodCategoryCount, FoodItemDetailOut, FoodItemSearchOut, FoodPortionOut
from app.services import food_service

router = APIRouter(prefix="/food_items", tags=["food items"])


@router.get("", response_model=PaginatedResponse[FoodItemSearchOut])
def search_food_items(
    q: str = Query(default="", min_length=0),
    source: str | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=FOOD_SEARCH_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = food_service.search_food_items(db, q, source, category, page, page_size)
    return make_paginated(
        [FoodItemSearchOut.model_validate(i) for i in items], total, page, page_size
    )


@router.get("/categories", response_model=list[FoodCategoryCount])
def get_categories(
    q: str = Query(default=""),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    results = food_service.get_food_categories(db, q)
    return [FoodCategoryCount(**r) for r in results]


@router.get("/recent", response_model=list[FoodItemSearchOut])
def get_recent(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = food_service.get_recent_foods(db, current_user.id, limit)
    return [FoodItemSearchOut.model_validate(i) for i in items]


@router.get("/{food_id}", response_model=FoodItemDetailOut)
def get_food_item(
    food_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item, portions = food_service.get_food_item(db, food_id)
    out = FoodItemDetailOut.model_validate(item)
    out.portions = [FoodPortionOut.model_validate(p) for p in portions]
    return out


@router.post("", response_model=FoodItemDetailOut, status_code=201)
def create_custom_food(
    req: CustomFoodItemIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = food_service.create_custom_food(db, current_user.id, req)
    out = FoodItemDetailOut.model_validate(item)
    out.portions = []
    return out


@router.patch("/{food_id}", response_model=FoodItemDetailOut)
def update_custom_food(
    food_id: str,
    req: CustomFoodItemIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = food_service.update_custom_food(db, current_user.id, food_id, req)
    out = FoodItemDetailOut.model_validate(item)
    out.portions = []
    return out


@router.delete("/{food_id}", status_code=204)
def delete_custom_food(
    food_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    food_service.delete_custom_food(db, current_user.id, food_id)

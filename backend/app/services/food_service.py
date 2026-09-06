import uuid
from datetime import datetime, timezone

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.food_item import FoodItem
from app.models.food_portion import FoodPortion
from app.models.meal_log import MealLog
from app.schemas.food_item import CustomFoodItemIn


def search_food_items(
    db: Session,
    q: str,
    source: str | None,
    category: str | None,
    page: int,
    page_size: int,
) -> tuple[list[FoodItem], int]:
    query = db.query(FoodItem)

    if q:
        query = query.filter(FoodItem.name.ilike(f"%{q}%"))
    if source:
        query = query.filter(FoodItem.source == source)
    if category:
        query = query.filter(FoodItem.category == category)

    total = query.with_entities(func.count()).scalar()

    if q:
        q_lower = q.lower()
        relevance = case(
            (func.lower(FoodItem.name) == q_lower,                   0),
            (func.lower(FoodItem.name).like(f"{q_lower}%"),          1),
            else_=2,
        )
        order = (relevance, FoodItem.name)
    else:
        order = (FoodItem.name,)

    items = query.order_by(*order).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_food_categories(db: Session, q: str) -> list[dict]:
    """Return categories with match counts for a query, ordered by count desc."""
    query = (
        db.query(FoodItem.category, func.count(FoodItem.id).label("count"))
        .filter(FoodItem.category.isnot(None))
    )
    if q:
        query = query.filter(FoodItem.name.ilike(f"%{q}%"))
    results = (
        query
        .group_by(FoodItem.category)
        .order_by(func.count(FoodItem.id).desc())
        .all()
    )
    return [{"category": r[0], "count": r[1]} for r in results]


def get_recent_foods(db: Session, user_id: str, limit: int = 5) -> list[FoodItem]:
    """Return the N most recently logged distinct food items for a user."""
    subq = (
        db.query(
            MealLog.food_item_id,
            func.max(MealLog.logged_at).label("last_used"),
        )
        .filter(MealLog.user_id == user_id, MealLog.food_item_id.isnot(None))
        .group_by(MealLog.food_item_id)
        .order_by(func.max(MealLog.logged_at).desc())
        .limit(limit)
        .subquery()
    )
    return (
        db.query(FoodItem)
        .join(subq, FoodItem.id == subq.c.food_item_id)
        .order_by(subq.c.last_used.desc())
        .all()
    )


def get_food_item(db: Session, food_id: str) -> tuple[FoodItem, list[FoodPortion]]:
    item = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not item:
        raise NotFoundError("Food item not found")
    portions = db.query(FoodPortion).filter(FoodPortion.food_item_id == food_id).all()
    return item, portions


def create_custom_food(db: Session, user_id: str, req: CustomFoodItemIn) -> FoodItem:
    item = FoodItem(
        id=str(uuid.uuid4()),
        source="user_custom",
        is_verified=False,
        created_by=user_id,
    )
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_custom_food(db: Session, user_id: str, food_id: str, req: CustomFoodItemIn) -> FoodItem:
    item = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not item:
        raise NotFoundError("Food item not found")
    if item.source != "user_custom" or item.created_by != user_id:
        raise ForbiddenError("Cannot edit this food item")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_custom_food(db: Session, user_id: str, food_id: str) -> None:
    item = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not item:
        raise NotFoundError("Food item not found")
    if item.source != "user_custom" or item.created_by != user_id:
        raise ForbiddenError("Cannot delete this food item")
    if db.query(MealLog).filter(MealLog.food_item_id == food_id).first():
        raise ConflictError("Food item is referenced by meal logs and cannot be deleted")
    db.delete(item)
    db.commit()

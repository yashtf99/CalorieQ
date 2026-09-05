import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.models.food_item import FoodItem
from app.models.meal_log import MealLog
from app.schemas.meal_log import MealLogIn, MealLogPatchIn


def _scale(per_100g, quantity_g: float) -> float | None:
    """SQLAlchemy Numeric columns return Decimal — cast to float before arithmetic."""
    if per_100g is None:
        return None
    return round(float(per_100g) * quantity_g / 100, 4)


def _assert_owned(log: MealLog, user_id: str) -> None:
    if log.user_id != user_id:
        raise ForbiddenError("Not your meal log")


def create_meal_log(db: Session, user_id: str, req: MealLogIn) -> MealLog:
    # Always store as naive UTC — SQLite has no timezone type.
    # Convert to UTC *before* stripping tzinfo so +05:30 offsets aren't silently treated as UTC.
    raw_logged_at = req.logged_at or datetime.now(timezone.utc)
    if raw_logged_at.tzinfo is not None:
        logged_at = raw_logged_at.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        logged_at = raw_logged_at

    if req.food_item_id:
        food = db.query(FoodItem).filter(FoodItem.id == req.food_item_id).first()
        if not food:
            raise NotFoundError("Food item not found")
        # Custom foods are private to their creator
        if food.source == "user_custom" and food.created_by != user_id:
            raise ForbiddenError("Food item not found")

        energy_kcal = _scale(food.energy_kcal, req.quantity_g)
        if energy_kcal is None:
            raise UnprocessableError("Food item has no calorie data")

        log = MealLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            food_item_id=food.id,
            food_name_snapshot=food.name,
            meal_type=req.meal_type,
            quantity_g=req.quantity_g,
            energy_kcal=energy_kcal,
            protein_g=_scale(food.protein_g, req.quantity_g) or 0.0,
            carb_g=_scale(food.carb_g, req.quantity_g) or 0.0,
            fat_g=_scale(food.fat_g, req.quantity_g) or 0.0,
            fibre_g=_scale(food.fibre_g, req.quantity_g),
            sodium_mg=_scale(food.sodium_mg, req.quantity_g),
            source=req.source,
            notes=req.notes,
            logged_at=logged_at,
        )
    else:
        log = MealLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            food_item_id=None,
            food_name_snapshot=req.food_name_snapshot,
            meal_type=req.meal_type,
            quantity_g=req.quantity_g,
            energy_kcal=req.energy_kcal,
            protein_g=req.protein_g or 0.0,
            carb_g=req.carb_g or 0.0,
            fat_g=req.fat_g or 0.0,
            fibre_g=req.fibre_g,
            sodium_mg=req.sodium_mg,
            source=req.source,
            notes=req.notes,
            logged_at=logged_at,
        )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_meal_logs(
    db: Session,
    user_id: str,
    date_start: datetime,
    date_end: datetime,
    meal_type: str | None,
    page: int,
    page_size: int,
) -> tuple[list[MealLog], int]:
    # Normalise to naive UTC — matches how logged_at is stored in SQLite
    start_naive = date_start.replace(tzinfo=None)
    end_naive = date_end.replace(tzinfo=None)

    q = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.logged_at >= start_naive,
        MealLog.logged_at < end_naive,
    )
    if meal_type:
        q = q.filter(MealLog.meal_type == meal_type)

    total = q.with_entities(func.count()).scalar()
    logs = q.order_by(MealLog.logged_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return logs, total


def get_meal_log(db: Session, user_id: str, log_id: str) -> MealLog:
    log = db.query(MealLog).filter(MealLog.id == log_id).first()
    if not log:
        raise NotFoundError("Meal log not found")
    _assert_owned(log, user_id)
    return log


def update_meal_log(db: Session, user_id: str, log_id: str, req: MealLogPatchIn) -> MealLog:
    log = get_meal_log(db, user_id, log_id)

    if req.meal_type is not None:
        log.meal_type = req.meal_type
    if req.logged_at is not None:
        if req.logged_at.tzinfo is not None:
            log.logged_at = req.logged_at.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            log.logged_at = req.logged_at
    if req.notes is not None:
        log.notes = req.notes

    if req.quantity_g is not None:
        log.quantity_g = req.quantity_g
        if log.food_item_id:
            # Linked entry — recalculate from food item
            food = db.query(FoodItem).filter(FoodItem.id == log.food_item_id).first()
            if food:
                energy_kcal = _scale(food.energy_kcal, req.quantity_g)
                if energy_kcal is None:
                    raise UnprocessableError("Food item has no calorie data")
                log.energy_kcal = energy_kcal
                log.protein_g = _scale(food.protein_g, req.quantity_g) or 0.0
                log.carb_g = _scale(food.carb_g, req.quantity_g) or 0.0
                log.fat_g = _scale(food.fat_g, req.quantity_g) or 0.0
                log.fibre_g = _scale(food.fibre_g, req.quantity_g)
                log.sodium_mg = _scale(food.sodium_mg, req.quantity_g)
        # Free-form entries: quantity updated but nutrition not auto-recalculated
        # (user must also supply updated nutrition fields if they want them changed)

    # Free-form nutrition overrides (only applied when entry has no food_item_id)
    if not log.food_item_id:
        if req.energy_kcal is not None:
            log.energy_kcal = req.energy_kcal
        if req.protein_g is not None:
            log.protein_g = req.protein_g
        if req.carb_g is not None:
            log.carb_g = req.carb_g
        if req.fat_g is not None:
            log.fat_g = req.fat_g
        if req.fibre_g is not None:
            log.fibre_g = req.fibre_g
        if req.sodium_mg is not None:
            log.sodium_mg = req.sodium_mg

    db.commit()
    db.refresh(log)
    return log


def delete_meal_log(db: Session, user_id: str, log_id: str) -> None:
    log = get_meal_log(db, user_id, log_id)
    db.delete(log)
    db.commit()

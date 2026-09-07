"""Chat agent tools — each tool creates its own DB session (thread-safe)."""

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz
from langchain.tools import tool

from app.core.exceptions import NotFoundError
from app.schemas.meal_log import MealLogIn
from app.services import (
    food_service,
    goal_service,
    meal_log_service,
    report_service,
)
from app.services.chat_agent.context import AgentContext
from app.services.report_service import week_bounds

logger = logging.getLogger(__name__)


@contextmanager
def _db():
    """Context manager: new session per tool call, commit on success, rollback on error."""
    session = AgentContext.get_new_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@tool
def search_foods(q: str, page_size: int = 5) -> list[dict]:
    """Search for foods in the database by name.

    Args:
        q: Food name to search for.
        page_size: Number of results, maximum 20.

    Returns:
        List of food items with nutritional information.
    """
    with _db() as db:
        items, _ = food_service.search_food_items(
            db, q=q, source=None, category=None, page=1, page_size=min(page_size, 20)
        )
        return [
            {
                "id": item.id,
                "name": item.name,
                "energy_kcal": float(item.energy_kcal) if item.energy_kcal else None,
                "protein_g": float(item.protein_g) if item.protein_g else None,
                "carb_g": float(item.carb_g) if item.carb_g else None,
                "fat_g": float(item.fat_g) if item.fat_g else None,
                "fibre_g": float(item.fibre_g) if item.fibre_g else None,
            }
            for item in items
        ]


@tool
def log_meal(
    food_item_id: str, meal_type: str, quantity_g: float, logged_at: Optional[str] = None
) -> dict:
    """Log a meal using a food item from the database (macros are auto-calculated).

    Use this when you have a valid food_item_id from search_foods and the user
    is happy with the database nutrition values.

    Args:
        food_item_id: UUID of the food item from search_foods.
        meal_type: breakfast, lunch, dinner, or snacks.
        quantity_g: Quantity in grams.
        logged_at: ISO 8601 timestamp. Defaults to now.

    Returns:
        Logged meal details.
    """
    user_id = AgentContext.get_user_id()
    logger.info(f"log_meal: user={user_id} food_item_id={food_item_id} meal_type={meal_type} quantity_g={quantity_g}")

    logged_at_dt = None
    if logged_at:
        logged_at_dt = datetime.fromisoformat(logged_at.replace("Z", "+00:00"))

    request = MealLogIn(
        food_item_id=food_item_id, meal_type=meal_type, quantity_g=quantity_g, logged_at=logged_at_dt
    )

    with _db() as db:
        meal = meal_log_service.create_meal_log(db, user_id, request)
        logger.info(f"log_meal: success meal_id={meal.id} energy_kcal={meal.energy_kcal}")
        return {
            "id": meal.id,
            "food_name": meal.food_name_snapshot,
            "meal_type": meal.meal_type,
            "quantity_g": float(meal.quantity_g),
            "energy_kcal": float(meal.energy_kcal),
            "protein_g": float(meal.protein_g),
            "carb_g": float(meal.carb_g),
            "fat_g": float(meal.fat_g),
        }


@tool
def log_free_form_meal(
    food_name: str,
    meal_type: str,
    quantity_g: float,
    energy_kcal: float,
    protein_g: Optional[float] = None,
    carb_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    logged_at: Optional[str] = None,
) -> dict:
    """Log a meal using user-provided nutrition values (no database food item needed).

    Use this when the user gives explicit calorie/macro values, or when the database
    food item's nutrition doesn't match what the user reported.

    Args:
        food_name: Name of the food (e.g. "Curd Rice", "Restaurant Biryani").
        meal_type: breakfast, lunch, dinner, or snacks.
        quantity_g: Quantity in grams.
        energy_kcal: Calories (required).
        protein_g: Protein in grams (optional).
        carb_g: Carbohydrates in grams (optional).
        fat_g: Fat in grams (optional).
        logged_at: ISO 8601 timestamp. Defaults to now.

    Returns:
        Logged meal details.
    """
    user_id = AgentContext.get_user_id()
    logger.info(f"log_free_form_meal: user={user_id} food_name={food_name!r} meal_type={meal_type} quantity_g={quantity_g} energy_kcal={energy_kcal}")

    logged_at_dt = None
    if logged_at:
        logged_at_dt = datetime.fromisoformat(logged_at.replace("Z", "+00:00"))

    request = MealLogIn(
        food_name_snapshot=food_name,
        meal_type=meal_type,
        quantity_g=quantity_g,
        energy_kcal=energy_kcal,
        protein_g=protein_g,
        carb_g=carb_g,
        fat_g=fat_g,
        logged_at=logged_at_dt,
        source="user",
    )

    with _db() as db:
        meal = meal_log_service.create_meal_log(db, user_id, request)
        logger.info(f"log_free_form_meal: success meal_id={meal.id} food={meal.food_name_snapshot!r}")
        return {
            "id": meal.id,
            "food_name": meal.food_name_snapshot,
            "meal_type": meal.meal_type,
            "quantity_g": float(meal.quantity_g),
            "energy_kcal": float(meal.energy_kcal),
            "protein_g": float(meal.protein_g),
            "carb_g": float(meal.carb_g),
            "fat_g": float(meal.fat_g),
        }


@tool
def get_daily_summary(date: Optional[str] = None) -> dict:
    """Get calorie and macro summary versus goals for a date.

    Args:
        date: YYYY-MM-DD format. Defaults to today.

    Returns:
        Daily totals with calories, macros, goals, and remaining targets.
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    user_id = AgentContext.get_user_id()
    with _db() as db:
        return report_service.get_daily_summary(db, user_id, date, "UTC")


@tool
def get_meal_history(date: Optional[str] = None, meal_type: Optional[str] = None) -> list[dict]:
    """Get meal history for a specific date.

    Args:
        date: YYYY-MM-DD format. Defaults to today.
        meal_type: Optional filter - breakfast, lunch, dinner, snacks.

    Returns:
        List of meals logged on that date.
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    user_id = AgentContext.get_user_id()
    day_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    with _db() as db:
        meals, _ = meal_log_service.list_meal_logs(
            db, user_id, day_start, day_end, meal_type, page=1, page_size=100
        )
        return [
            {
                "id": meal.id,
                "food_name": meal.food_name_snapshot,
                "meal_type": meal.meal_type,
                "quantity_g": float(meal.quantity_g),
                "energy_kcal": float(meal.energy_kcal),
                "protein_g": float(meal.protein_g),
                "carb_g": float(meal.carb_g),
                "fat_g": float(meal.fat_g),
            }
            for meal in meals
        ]


@tool
def get_active_goal() -> Optional[dict]:
    """Get the user's currently active calorie and macro goals.

    Returns:
        Active goal object or None if no goal set.
    """
    user_id = AgentContext.get_user_id()
    with _db() as db:
        try:
            goal = goal_service.get_active_goal(db, user_id)
        except NotFoundError:
            return None

        return {
            "goal_type": goal.goal_type,
            "daily_calories": float(goal.daily_calories) if goal.daily_calories else None,
            "protein_g": float(goal.protein_g) if goal.protein_g else None,
            "carbs_g": float(goal.carbs_g) if goal.carbs_g else None,
            "fat_g": float(goal.fat_g) if goal.fat_g else None,
        }


@tool
def set_calorie_goal(
    goal_type: str,
    daily_calories: float,
    protein_g: Optional[float] = None,
    carbs_g: Optional[float] = None,
    fat_g: Optional[float] = None,
) -> dict:
    """Set or update the user's daily calorie goal.

    Args:
        goal_type: lose, maintain, or gain.
        daily_calories: Daily calorie target.
        protein_g: Daily protein target in grams (optional).
        carbs_g: Daily carbs target in grams (optional).
        fat_g: Daily fat target in grams (optional).

    Returns:
        New goal object.
    """
    from app.schemas.goal import GoalIn

    user_id = AgentContext.get_user_id()
    req = GoalIn(
        goal_type=goal_type,
        daily_calories=daily_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )

    with _db() as db:
        goal = goal_service.create_goal(db, user_id, req)
        return {
            "goal_type": goal.goal_type,
            "daily_calories": float(goal.daily_calories) if goal.daily_calories else None,
            "protein_g": float(goal.protein_g) if goal.protein_g else None,
            "carbs_g": float(goal.carbs_g) if goal.carbs_g else None,
            "fat_g": float(goal.fat_g) if goal.fat_g else None,
        }


@tool
def get_weekly_report(week_of: Optional[str] = None) -> dict:
    """Get weekly summary of calories, macros, and weight.

    Args:
        week_of: Date in YYYY-MM-DD format (snaps to the containing Sun-Sat week). Defaults to current week.

    Returns:
        Weekly report with daily breakdown and averages.
    """
    if not week_of:
        week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    user_id = AgentContext.get_user_id()
    anchor = datetime.strptime(week_of, "%Y-%m-%d").date()
    start_d, end_d = week_bounds(anchor)

    with _db() as db:
        return report_service.get_weekly_report(db, user_id, start_d, end_d, pytz.utc)


@tool
def delete_meal(meal_id: str) -> dict:
    """Delete a previously logged meal.

    Args:
        meal_id: UUID of the meal to delete.

    Returns:
        Confirmation message.
    """
    user_id = AgentContext.get_user_id()
    with _db() as db:
        meal_log_service.delete_meal_log(db, meal_id, user_id)
        return {"message": f"Meal {meal_id} deleted"}

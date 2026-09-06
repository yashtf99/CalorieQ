"""Chat agent tools for CalorieQ - tools manage their own context."""

from datetime import datetime, timezone
from typing import Optional

from langchain.tools import tool

from app.schemas.meal_log import MealLogIn
from app.services import (
    food_service,
    goal_service,
    meal_log_service,
    report_service,
)
from app.services.chat_agent.context import AgentContext


@tool
def search_foods(q: str, page_size: int = 5) -> list[dict]:
    """Search for foods in the database by name.

    Args:
        q: Food name to search for.
        page_size: Number of results, maximum 20.

    Returns:
        List of food items with nutritional information.
    """
    db = AgentContext.get_db()
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
    """Log a meal for the current user.

    Args:
        food_item_id: UUID of the food item.
        meal_type: breakfast, lunch, dinner, or snacks.
        quantity_g: Quantity in grams.
        logged_at: ISO 8601 timestamp. Defaults to now.

    Returns:
        Logged meal details.
    """
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    logged_at_dt = None
    if logged_at:
        logged_at_dt = datetime.fromisoformat(logged_at.replace("Z", "+00:00"))

    request = MealLogIn(
        food_item_id=food_item_id, meal_type=meal_type, quantity_g=quantity_g, logged_at=logged_at_dt
    )
    meal = meal_log_service.create_meal_log(db, user_id, request)
    db.commit()

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
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    summary = report_service.get_daily_summary(db, user_id, date, tz="UTC")

    return {
        "date": summary.date,
        "consumed": {
            "energy_kcal": float(summary.consumed.energy_kcal) if summary.consumed else None,
            "protein_g": float(summary.consumed.protein_g) if summary.consumed else None,
            "carb_g": float(summary.consumed.carb_g) if summary.consumed else None,
            "fat_g": float(summary.consumed.fat_g) if summary.consumed else None,
        },
        "goal": (
            {
                "daily_calories": float(summary.goal.daily_calories) if summary.goal.daily_calories else None,
                "protein_g": float(summary.goal.protein_g) if summary.goal.protein_g else None,
                "carbs_g": float(summary.goal.carbs_g) if summary.goal.carbs_g else None,
                "fat_g": float(summary.goal.fat_g) if summary.goal.fat_g else None,
            }
            if summary.goal
            else None
        ),
        "remaining": (
            {
                "energy_kcal": float(summary.remaining.energy_kcal) if summary.remaining.energy_kcal else None,
                "protein_g": float(summary.remaining.protein_g) if summary.remaining.protein_g else None,
                "carbs_g": float(summary.remaining.carbs_g) if summary.remaining.carbs_g else None,
                "fat_g": float(summary.remaining.fat_g) if summary.remaining.fat_g else None,
            }
            if summary.remaining
            else None
        ),
        "meals_tracked": summary.meals_tracked,
    }


@tool
def get_meal_history(date: Optional[str] = None, meal_type: Optional[str] = None) -> list[dict]:
    """Get meal history for a specific date.

    Args:
        date: YYYY-MM-DD format. Defaults to today.
        meal_type: Optional filter - breakfast, lunch, dinner, snacks.

    Returns:
        List of meals logged on that date.
    """
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    meals = meal_log_service.list_meal_logs(
        db, user_id=user_id, date=date, meal_type=meal_type, page=1, page_size=100
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
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    goal = goal_service.get_active_goal(db, user_id)

    if not goal:
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
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    from app.schemas.goal import GoalIn

    req = GoalIn(
        goal_type=goal_type,
        daily_calories=daily_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )
    goal = goal_service.create_goal(db, user_id, req)
    db.commit()

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
        week_of: Date in YYYY-MM-DD format (will snap to Sun-Sat week).

    Returns:
        Weekly report with daily breakdown and averages.
    """
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    if not week_of:
        week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report = report_service.get_weekly_report(db, user_id, week_of=week_of, tz="UTC")

    return {
        "start": report.start,
        "end": report.end,
        "days_with_logs": report.days_with_logs,
        "actual_period_avg": {
            "energy_kcal": float(report.actual_period_avg.energy_kcal),
            "protein_g": float(report.actual_period_avg.protein_g),
            "carb_g": float(report.actual_period_avg.carb_g),
            "fat_g": float(report.actual_period_avg.fat_g),
        },
        "data": [
            {
                "date": d.date,
                "energy_kcal": float(d.energy_kcal),
                "protein_g": float(d.protein_g),
                "carb_g": float(d.carb_g),
                "fat_g": float(d.fat_g),
            }
            for d in report.data
        ],
    }


@tool
def delete_meal(meal_id: str) -> dict:
    """Delete a previously logged meal.

    Args:
        meal_id: UUID of the meal to delete.

    Returns:
        Confirmation message.
    """
    db = AgentContext.get_db()
    user_id = AgentContext.get_user_id()

    meal_log_service.delete_meal_log(db, meal_id, user_id)
    db.commit()

    return {"message": f"Meal {meal_id} deleted"}

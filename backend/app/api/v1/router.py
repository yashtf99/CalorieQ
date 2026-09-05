from fastapi import APIRouter

from app.api.v1 import auth, food_items, goals, meals, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(goals.router)
router.include_router(food_items.router)
router.include_router(meals.router)

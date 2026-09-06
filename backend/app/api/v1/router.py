from fastapi import APIRouter

from app.api.v1 import ai, auth, chat, food_items, goals, meals, reports, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(goals.router)
router.include_router(food_items.router)
router.include_router(meals.router)
router.include_router(reports.router)
router.include_router(ai.router)
router.include_router(chat.router)

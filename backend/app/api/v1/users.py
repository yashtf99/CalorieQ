from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.user import User
from app.orm.session import get_db
from app.schemas.user import UserOut, UserProfileIn, UserProfileOut, UserUpdateIn
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def patch_me(
    req: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_user(db, current_user, req)


@router.get("/me/profile", response_model=UserProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.get_profile(db, current_user.id)


@router.patch("/me/profile", response_model=UserProfileOut)
def patch_profile(
    req: UserProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_profile(db, current_user.id, req)

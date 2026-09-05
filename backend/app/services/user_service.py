import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.weight_log import WeightLog
from app.schemas.user import UserProfileIn, UserUpdateIn


# ── /users/me ─────────────────────────────────────────────────────────────────

def update_user(db: Session, user: User, req: UserUpdateIn) -> User:
    if req.display_name is not None:
        user.display_name = req.display_name
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
    return user


# ── /users/me/profile ─────────────────────────────────────────────────────────

def _latest_weight(db: Session, user_id: str) -> WeightLog | None:
    return (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_at.desc())
        .first()
    )


def _build_profile_dict(user_id: str, profile: UserProfile | None, weight: WeightLog | None) -> dict:
    return {
        "user_id": user_id,
        "dob": profile.dob if profile else None,
        "gender": profile.gender if profile else None,
        "height_cm": float(profile.height_cm) if profile and profile.height_cm is not None else None,
        "activity_level": profile.activity_level if profile else None,
        "current_weight_kg": float(weight.weight_kg) if weight else None,
        "updated_at": profile.updated_at if profile else None,
    }


def get_profile(db: Session, user_id: str) -> dict:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    # Always query latest weight — a weight_log row can exist even when no profile row does
    latest_weight = _latest_weight(db, user_id)
    return _build_profile_dict(user_id, profile, latest_weight)


def update_profile(db: Session, user_id: str, req: UserProfileIn) -> dict:
    has_profile_fields = any(
        v is not None for v in (req.dob, req.gender, req.height_cm, req.activity_level)
    )
    has_weight = req.current_weight_kg is not None

    # No-op: nothing to write — avoid spurious row creation / updated_at bump
    if not has_profile_fields and not has_weight:
        return get_profile(db, user_id)

    if has_profile_fields:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)

        if req.dob is not None:
            profile.dob = req.dob
        if req.gender is not None:
            profile.gender = req.gender
        if req.height_cm is not None:
            profile.height_cm = req.height_cm
        if req.activity_level is not None:
            profile.activity_level = req.activity_level

        profile.updated_at = datetime.now(timezone.utc)

    if has_weight:
        db.add(WeightLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            weight_kg=req.current_weight_kg,
            logged_at=datetime.now(timezone.utc),
        ))

    db.commit()
    return get_profile(db, user_id)

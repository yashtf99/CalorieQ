import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from config import settings


def _issue_tokens(db: Session, user_id: str) -> tuple[str, str]:
    access_token = create_access_token(user_id)
    raw_refresh = generate_refresh_token()

    rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()

    return access_token, raw_refresh


def register(db: Session, req: RegisterRequest) -> tuple[User, str, str]:
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email already registered")
    db.refresh(user)

    access_token, refresh_token = _issue_tokens(db, user.id)
    return user, access_token, refresh_token


def login(db: Session, req: LoginRequest) -> tuple[str, str]:
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    return _issue_tokens(db, user.id)


def refresh(db: Session, raw_token: str) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_token)
    now = datetime.now(timezone.utc)

    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    # Treat missing, revoked, or expired tokens identically — no info leakage
    if not rt or rt.revoked:
        raise UnauthorizedError("Refresh token invalid or expired")

    # expires_at comes back from SQLite as a naive datetime — attach UTC for comparison
    expires_at = rt.expires_at if rt.expires_at.tzinfo else rt.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise UnauthorizedError("Refresh token invalid or expired")

    rt.revoked = True
    db.commit()

    return _issue_tokens(db, rt.user_id)


def logout(db: Session, raw_token: str) -> None:
    token_hash = hash_refresh_token(raw_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt and not rt.revoked:
        rt.revoked = True
        db.commit()

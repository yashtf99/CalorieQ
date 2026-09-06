"""Chat session management service."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from config import settings


def create_session(db: Session, user_id: str, title: Optional[str] = None) -> ChatSession:
    """Create a new chat session for the user."""
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
    )
    db.add(session)
    db.commit()
    return session


def get_session(db: Session, session_id: str, user_id: str) -> ChatSession:
    """Get a chat session, ensuring user ownership."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()

    if not session:
        raise NotFoundError("Chat session not found")

    return session


def list_sessions(db: Session, user_id: str, limit: int = 20) -> list[ChatSession]:
    """List user's chat sessions, most recent first."""
    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.updated_at.desc()).limit(limit).all()


def add_message(
    db: Session,
    session_id: str,
    user_id: str,
    user_query: str,
    chat_response: str,
) -> ChatMessage:
    """Add a message pair to a session."""
    session = get_session(db, session_id, user_id)

    message = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        user_query=user_query,
        chat_response=chat_response,
    )
    db.add(message)

    session.updated_at = datetime.utcnow()

    db.commit()
    return message


def get_session_messages(db: Session, session_id: str, user_id: str) -> list[ChatMessage]:
    """Get all messages in a session."""
    session = get_session(db, session_id, user_id)

    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()


def delete_session(db: Session, session_id: str, user_id: str) -> None:
    """Delete a chat session and all its messages."""
    session = get_session(db, session_id, user_id)

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()


def get_or_create_session(db: Session, user_id: str) -> ChatSession:
    """Get the user's most recent active session or create a new one.

    A session is considered active if it was updated within the configured timeout window.
    Otherwise, create a new session.
    """
    # Get the most recent session
    recent_session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.updated_at.desc()).first()

    if recent_session:
        # Check if it's still within the timeout window
        timeout_threshold = datetime.now(timezone.utc) - timedelta(
            minutes=settings.CHAT_SESSION_TIMEOUT_MINUTES
        )
        # Compare without timezone info since DB stores naive UTC
        recent_update = recent_session.updated_at.replace(tzinfo=None)
        if recent_update > timeout_threshold.replace(tzinfo=None):
            return recent_session

    # Create a new session
    return create_session(db, user_id)

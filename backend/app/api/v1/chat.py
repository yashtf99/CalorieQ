"""Chat agent endpoint."""

from typing import Optional
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from langchain_core.messages import HumanMessage

from app.api.deps import get_current_user
from app.models.user import User
from app.orm.session import get_db
from app.services.chat_agent.agent import get_agent
from app.services.chat_agent.context import AgentContext
from app.services.chat_agent.history import DatabaseChatMessageHistory
from app.services.chat_session_service import (
    create_session,
    get_session,
    list_sessions as list_user_sessions,
    delete_session as delete_user_session,
    add_message,
    get_session_messages,
    get_or_create_session,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    response: str
    session_id: str


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class ChatMessageOut(BaseModel):
    user_query: str
    chat_response: str
    created_at: str


@router.post("/sessions")
def create_new_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    session = create_session(db, user.id)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get("/sessions")
def get_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SessionResponse]:
    sessions = list_user_sessions(db, user.id)
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    msgs = get_session_messages(db, session_id, user.id)
    return [
        ChatMessageOut(
            user_query=m.user_query,
            chat_response=m.chat_response,
            created_at=m.created_at.isoformat(),
        )
        for m in msgs
    ]


@router.delete("/sessions/{session_id}")
def remove_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    delete_user_session(db, session_id, user.id)
    return {"message": "Session deleted"}


@router.post("/message")
def send_message(
    req: MessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Send a message. Uses req.session_id if provided, otherwise auto-selects session."""
    session = None
    try:
        if req.session_id:
            session = get_session(db, req.session_id, user.id)
        else:
            session = get_or_create_session(db, user.id)

        AgentContext.set(user.id, db)

        agent = get_agent()

        history = DatabaseChatMessageHistory(session.id, user.id, db)
        chat_history = history.messages

        result = agent.invoke({
            "messages": [*chat_history, HumanMessage(content=req.message)],
        })

        response_text = result["messages"][-1].content if result.get("messages") else "I couldn't process that. Please try again."

        add_message(
            db,
            session.id,
            user.id,
            user_query=req.message,
            chat_response=response_text,
        )

        return MessageResponse(response=response_text, session_id=session.id)

    except Exception:
        logger.exception("Chat endpoint error")
        if session:
            return MessageResponse(
                response="An error occurred. Please try again.",
                session_id=session.id,
            )
        raise
    finally:
        try:
            AgentContext.clear()
        except Exception:
            pass

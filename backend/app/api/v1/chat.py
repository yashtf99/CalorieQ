"""Chat agent endpoint."""

from typing import Optional
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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


class MessageResponse(BaseModel):
    response: str
    session_id: str


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


@router.post("/sessions")
def create_new_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Create a new chat session for the user."""
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
    """List user's chat sessions."""
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


@router.delete("/sessions/{session_id}")
def remove_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a chat session."""
    delete_user_session(db, session_id, user.id)
    return {"message": "Session deleted"}


@router.post("/message")
def send_message(
    req: MessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Send a message and get or create a session automatically.

    Lazy creates session on first message, reuses within timeout window.

    Args:
        message: User's query

    Returns:
        Assistant's response with session ID
    """
    session = None
    try:
        logger.info(f"Chat message from user {user.id}: {req.message}")

        # Get or create session (lazy creation)
        logger.info("Creating/fetching session")
        session = get_or_create_session(db, user.id)
        logger.info(f"Got session {session.id}")

        # Set context for tools (tools will retrieve this)
        logger.info("Setting agent context")
        AgentContext.set(user.id, db)

        # Get agent (independent, no user/session coupling)
        logger.info("Getting agent")
        agent = get_agent()
        logger.info("Agent obtained")

        # Load conversation history for this session
        logger.info("Loading chat history")
        history = DatabaseChatMessageHistory(session.id, user.id, db)
        chat_history = history.messages
        logger.info(f"Loaded {len(chat_history)} messages")

        # Invoke agent with history
        logger.info("Invoking agent")
        try:
            result = agent.invoke({
                "messages": [*chat_history, {"role": "user", "content": req.message}],
            })
            logger.info("Agent invocation successful")
        except Exception as tool_error:
            logger.error(f"Agent invocation failed: {tool_error}", exc_info=True)
            # Return a user-friendly error message
            return MessageResponse(
                response="I encountered an error processing your request. Please try again.",
                session_id=session.id
            )

        # Extract response from result
        logger.info("Extracting response from result")
        response_text = result["messages"][-1].content if result.get("messages") else "I couldn't process that. Please try again."
        logger.info(f"Got response: {response_text[:100]}")

        # Save message to database
        logger.info("Saving message to database")
        add_message(
            db,
            session.id,
            user.id,
            user_query=req.message,
            chat_response=response_text,
        )
        logger.info("Message saved")

        return MessageResponse(response=response_text, session_id=session.id)

    except Exception as e:
        logger.exception("Chat endpoint error")
        if session:
            return MessageResponse(
                response="An error occurred. Please try again.",
                session_id=session.id
            )
        raise
    finally:
        # Clear context after use
        try:
            AgentContext.clear()
        except Exception:
            pass

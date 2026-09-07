"""Agent runtime context — uses contextvars so it propagates into thread pool workers.

Tools must call get_new_db() to get a thread-local session they own (commit + close it themselves).
SQLAlchemy sessions are not thread-safe; sharing the request session across threads causes errors.
"""

import contextvars
import logging
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

_user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)
_session_factory_var: contextvars.ContextVar[Optional[sessionmaker]] = contextvars.ContextVar("session_factory", default=None)


class AgentContext:
    """Manages request-specific context for agent tools."""

    @staticmethod
    def set(user_id: str, db: Session) -> None:
        logger.debug(f"Setting context for user {user_id}")
        _user_id_var.set(user_id)
        # Derive factory from the request session's engine — correct for both prod and tests
        factory = sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False)
        _session_factory_var.set(factory)

    @staticmethod
    def get_user_id() -> str:
        value = _user_id_var.get()
        if value is None:
            logger.error("User context not set")
            raise RuntimeError("User context not set. Call AgentContext.set() first.")
        return value

    @staticmethod
    def get_new_db() -> Session:
        """Create a new independent session owned by the caller. Caller must commit/rollback and close it."""
        factory = _session_factory_var.get()
        if factory is None:
            raise RuntimeError("Session factory not set. Call AgentContext.set() first.")
        return factory()

    @staticmethod
    def clear() -> None:
        logger.debug("Clearing context")
        _user_id_var.set(None)
        _session_factory_var.set(None)

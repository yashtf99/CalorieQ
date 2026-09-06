"""Agent runtime context - thread-local storage for tools."""

import threading
from typing import Optional

from sqlalchemy.orm import Session

# Thread-local storage for context
_context = threading.local()


class AgentContext:
    """Manages request-specific context for agent tools."""

    @staticmethod
    def set(user_id: str, db: Session) -> None:
        """Set the current context."""
        _context.user_id = user_id
        _context.db = db

    @staticmethod
    def get_user_id() -> str:
        """Get the current user ID from context."""
        if not hasattr(_context, "user_id"):
            raise RuntimeError("User context not set. Call AgentContext.set() first.")
        return _context.user_id

    @staticmethod
    def get_db() -> Session:
        """Get the current database session from context."""
        if not hasattr(_context, "db"):
            raise RuntimeError("Database context not set. Call AgentContext.set() first.")
        return _context.db

    @staticmethod
    def clear() -> None:
        """Clear the current context."""
        if hasattr(_context, "user_id"):
            delattr(_context, "user_id")
        if hasattr(_context, "db"):
            delattr(_context, "db")

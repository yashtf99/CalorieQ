"""Database-backed chat message history."""

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from app.services import chat_session_service


class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """Chat message history backed by database."""

    def __init__(self, session_id: str, user_id: str, db: Session):
        self.session_id = session_id
        self.user_id = user_id
        self.db = db

    @property
    def messages(self) -> list[BaseMessage]:
        """Load messages from database."""
        db_messages = chat_session_service.get_session_messages(
            self.db, self.session_id, self.user_id
        )
        messages = []
        for msg in db_messages:
            messages.append(HumanMessage(content=msg.user_query))
            messages.append(AIMessage(content=msg.chat_response))
        return messages

    def add_user_message(self, message: str) -> None:
        """Add a user message (called before agent processing)."""
        pass

    def add_ai_message(self, message: str) -> None:
        """Add an AI message (called after agent processing)."""
        pass

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""
        pass

    def clear(self) -> None:
        """Clear the message history."""
        pass

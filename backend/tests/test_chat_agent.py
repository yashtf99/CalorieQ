"""Tests for the chat agent graph — mocks Bedrock so no AWS credentials needed."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.security import hash_password
from app.models.user import User
from app.services.chat_agent.context import AgentContext


@pytest.fixture
def user(db):
    u = User(
        id=str(uuid.uuid4()),
        email="agent@test.com",
        password_hash=hash_password("testpass"),
        display_name="Agent Tester",
    )
    db.add(u)
    db.commit()
    return u


def _make_mock_model(responses: list[AIMessage]):
    """Return a mock that behaves like a bound ChatBedrockConverse."""
    mock = MagicMock()
    mock.bind_tools.return_value = mock
    mock.invoke.side_effect = responses
    return mock


def test_agent_no_tool_call(db, user):
    """Agent returns a direct answer without invoking any tool."""
    AgentContext.set(user.id, db)

    mock_model = _make_mock_model([
        AIMessage(content="Hello! I can help you track your nutrition."),
    ])

    with patch("app.services.chat_agent.agent.ChatBedrockConverse", return_value=mock_model):
        from app.services.chat_agent.agent import get_agent
        agent = get_agent()
        result = agent.invoke({"messages": [HumanMessage(content="Hi")]})

    final = result["messages"][-1]
    assert final.content == "Hello! I can help you track your nutrition."
    assert mock_model.invoke.call_count == 1

    AgentContext.clear()


def test_agent_tool_call_roundtrip(db, user):
    """Agent calls get_active_goal tool, receives result, then responds."""
    AgentContext.set(user.id, db)

    mock_model = _make_mock_model([
        # First turn: request tool call
        AIMessage(
            content="",
            tool_calls=[{"id": "call_1", "name": "get_active_goal", "args": {}}],
        ),
        # Second turn: respond after seeing tool result
        AIMessage(content="You have no active goal set yet."),
    ])

    with patch("app.services.chat_agent.agent.ChatBedrockConverse", return_value=mock_model):
        from app.services.chat_agent.agent import get_agent
        agent = get_agent()
        result = agent.invoke({"messages": [HumanMessage(content="What's my goal?")]})

    # Model should have been called twice: initial + after tool result
    assert mock_model.invoke.call_count == 2

    final = result["messages"][-1]
    assert final.content == "You have no active goal set yet."

    # ToolMessage for get_active_goal should be in the message chain
    tool_messages = [m for m in result["messages"] if hasattr(m, "tool_call_id")]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "get_active_goal"

    AgentContext.clear()


def test_agent_search_foods_tool(db, user):
    """Agent calls search_foods and the tool actually queries the DB."""
    AgentContext.set(user.id, db)

    mock_model = _make_mock_model([
        AIMessage(
            content="",
            tool_calls=[{"id": "call_2", "name": "search_foods", "args": {"q": "chicken"}}],
        ),
        AIMessage(content="I found some chicken items in the database."),
    ])

    with patch("app.services.chat_agent.agent.ChatBedrockConverse", return_value=mock_model):
        from app.services.chat_agent.agent import get_agent
        agent = get_agent()
        result = agent.invoke({"messages": [HumanMessage(content="Search for chicken")]})

    assert mock_model.invoke.call_count == 2

    tool_messages = [m for m in result["messages"] if hasattr(m, "tool_call_id")]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "search_foods"
    # Tool ran against the real (empty test) DB — content is a list directly
    assert isinstance(tool_messages[0].content, list)

    AgentContext.clear()

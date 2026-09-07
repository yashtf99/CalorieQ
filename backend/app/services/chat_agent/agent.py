"""Chat agent — explicit 2-node LangGraph ReAct loop."""

from typing import Annotated

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from app.services.chat_agent.tools import (
    delete_meal,
    get_active_goal,
    get_daily_summary,
    get_meal_history,
    get_weekly_report,
    log_free_form_meal,
    log_meal,
    search_foods,
    set_calorie_goal,
)
from config import settings

_SYSTEM_PROMPT = """You are the CalorieQ assistant, a nutrition tracking tool. Help users log meals, check daily/weekly summaries, and manage goals using the available tools.

## Guidelines
- Use tools to fetch real data before responding; never estimate nutrition values
- Ask for clarification when a request is ambiguous; confirm before modifying or deleting data
- Stay within meal logging, goals, and reports — no medical advice, diet plans, or cross-user data
- Never re-log a meal you already confirmed as logged in this conversation — if the user asks again, remind them it was already logged

## Tool Mapping
- "What did I eat today?" → get_daily_summary()
- "Log [food] for [meal]" → search_foods() first; if user provides custom nutrition values use log_free_form_meal(), otherwise use log_meal() with the database food_item_id
- "How was my week?" → get_weekly_report()
- "What's my goal?" → get_active_goal()"""

_TOOLS = [
    search_foods,
    log_meal,
    log_free_form_meal,
    get_daily_summary,
    get_meal_history,
    get_active_goal,
    set_calorie_goal,
    get_weekly_report,
    delete_meal,
]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def get_agent():
    """Build a LangGraph ReAct agent graph."""
    model = ChatBedrockConverse(
        model=settings.BEDROCK_MODEL_ID,
        region_name=settings.AWS_REGION,
    ).bind_tools(_TOOLS)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [model.invoke(messages)]}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(_TOOLS, handle_tool_errors=True))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()

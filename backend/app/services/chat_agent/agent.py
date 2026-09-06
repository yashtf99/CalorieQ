"""Chat agent creation and configuration."""

from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse

from app.services.chat_agent.tools import (
    delete_meal,
    get_active_goal,
    get_daily_summary,
    get_meal_history,
    get_weekly_report,
    log_meal,
    search_foods,
    set_calorie_goal,
)
from config import settings


def get_agent():
    """Get a configured LangChain agent for CalorieQ nutrition tracking.

    Returns:
        Compiled agent graph ready to invoke with messages.
    """
    tools = [
        search_foods,
        log_meal,
        get_daily_summary,
        get_meal_history,
        get_active_goal,
        set_calorie_goal,
        get_weekly_report,
        delete_meal,
    ]

    model = ChatBedrockConverse(
        model=settings.BEDROCK_MODEL_ID,
        region_name=settings.AWS_REGION,
    )

    system_prompt = """You are the CalorieQ assistant, a nutrition tracking tool. Help users log meals, check daily/weekly summaries, and manage goals using the available tools.

## Guidelines
- Use tools to fetch real data before responding; never estimate nutrition values
- Ask for clarification when a request is ambiguous; confirm before modifying or deleting data
- Stay within meal logging, goals, and reports — no medical advice, diet plans, or cross-user data

## Tool Mapping
- "What did I eat today?" → get_daily_summary()
- "Log [food] for [meal]" → search_foods() → log_meal()
- "How was my week?" → get_weekly_report()
- "What's my goal?" → get_active_goal()"""

    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
    )

    return agent


if __name__ == "__main__":
    """Simple test of the decoupled chat agent."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from app.core.aws_init import ensure_aws_credentials

    ensure_aws_credentials()

    try:
        # Get agent (no parameters - stateless)
        agent = get_agent()
        print("[INFO] Agent initialized")

        # Test queries
        test_queries = [
            "What's my calorie goal?",
            "Can you search for chicken?",
            "Show me what I ate today",
        ]

        for query in test_queries:
            print(f"\n[QUERY] {query}")
            print("=" * 60)

            result = agent.invoke({"messages": [{"role": "user", "content": query}]})

            if isinstance(result, dict) and result.get("messages"):
                response = result["messages"][-1].content
                print(f"[RESPONSE] {response}")
            else:
                print(f"[RESPONSE] {result}")

        print("=" * 60)
        print("[SUCCESS] Agent test completed!")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

import json
from typing import Literal, Self, cast

from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command as LanggraphCommand
from pydantic import BaseModel

from foreign_exchange.client import ForeignExchangeClient
from foreign_exchange.conf import settings
from foreign_exchange.currencies import (
    CURRENCIES,
    Currencies,
)

assert settings.openai_api_key


ForeignExchangeGraphNodes = Literal[
    "get_user_currency_input_node",
    "determine_currency_and_get_rates_node",
    "end_node",
    "failure_node",
]

ForeignExchangeGraphCommand = LanggraphCommand[ForeignExchangeGraphNodes]


class ForeignExchangeGraphState(BaseModel):
    raw_user_input: str | None
    user_currency_input: Currencies | None
    failure_message: str | None
    rates: dict[Currencies, float]

    def set_raw_user_input(self, raw_user_input: str) -> Self:
        new_state = self.model_copy()
        new_state.raw_user_input = raw_user_input

        return new_state

    def set_user_currency_input(self, user_currency_input: Currencies) -> Self:
        new_state = self.model_copy()
        new_state.user_currency_input = user_currency_input

        return new_state

    def set_failure_message(self, failure_message: str) -> Self:
        new_state = self.model_copy()
        new_state.failure_message = failure_message

        return new_state

    def set_rates(self, rates: dict[Currencies, float]) -> Self:
        new_state = self.model_copy()
        new_state.rates = rates

        return new_state


foreign_exchange_client = ForeignExchangeClient()


@tool
async def get_exchange_rates(base_currency: str) -> dict[Currencies, float]:
    """Get current foreign exchange rates for a base currency.

    Args:
        base_currency: The 3-letter currency code to use as base (e.g., 'USD', 'EUR', 'GBP')

    Returns:
        Dictionary mapping currency codes to their exchange rates relative to the base currency
    """

    base_currency_upper = base_currency.strip().upper()
    if base_currency_upper not in CURRENCIES:
        raise ValueError(
            f"Unsupported currency: {base_currency}. Must be one of: {', '.join(CURRENCIES)}"
        )

    # Cast to proper type since we validated above
    validated_base_currency = cast(Currencies, base_currency_upper)

    try:
        response = await foreign_exchange_client.get_rates(base=validated_base_currency)
    except Exception as e:
        raise RuntimeError(
            f"Failed to get exchange rates for '{base_currency}': {str(e)}"
        )

    return response.rates


gpt4o_mini_agent = create_react_agent("openai:gpt-4o-mini", tools=[get_exchange_rates])


def get_user_currency_input_node(
    state: ForeignExchangeGraphState,
) -> ForeignExchangeGraphCommand:
    user_currency_input = state.raw_user_input
    if user_currency_input:
        return ForeignExchangeGraphCommand(
            update=state, goto="determine_currency_and_get_rates_node"
        )

    try:
        user_currency_input = input(
            "Which currency do you want to know the rates of today?\n"
        ).strip()
    except Exception:
        pass

    if not user_currency_input:
        return ForeignExchangeGraphCommand(
            update=state.set_failure_message("Invalid user input"), goto="failure_node"
        )

    return ForeignExchangeGraphCommand(
        update=state.set_raw_user_input(user_currency_input),
        goto="determine_currency_and_get_rates_node",
    )


def failure_node(state: ForeignExchangeGraphState) -> ForeignExchangeGraphState:
    assert state.failure_message

    print(state.failure_message)

    return state


async def determine_currency_and_get_rates_node(
    state: ForeignExchangeGraphState,
) -> ForeignExchangeGraphCommand:
    """
    Use the AI model with the exchange rates tool to:
    1. Identify the currency from user input
    2. Automatically call the get_exchange_rates tool
    3. Return the rates data
    """
    assert state.raw_user_input

    currency_and_rates_prompt = f"""
You are a helpful foreign exchange assistant with access to real-time currency data.

The user said: "{state.raw_user_input}"

CRITICAL: The input MUST be explicitly about currencies, money, or exchange rates.

STRICT CURRENCY IDENTIFICATION RULES:
- The input must contain clear, unambiguous currency-related content
- Acceptable inputs ONLY include:
  * Currency codes (USD, EUR, GBP, etc.)
  * Currency names (Dollar, Euro, Pound, Yen, etc.)
  * Country names when asking about their currency (United States, Germany, Japan, etc.)
  * Nationalities when asking about their currency (American, German, Japanese, etc.)
  * Currency names in other languages (Dólar, Euro, Libra, etc.)
  * Explicit currency questions ("What's the rate for...", "How much is the Euro worth?")

IMMEDIATELY REJECT ALL inputs that are NOT directly currency-related:
- Expressions of uncertainty: "I don't know", "I'm not sure", "Maybe", "Dunno", "No idea"
- Vague responses: "Unknown", "Test", "Random", "Something", "Anything"
- Unrelated phrases: "Let me in please", "Hello", "Help me", "Show me something"
- Commands or requests not about currency: "Open this", "Give me access", "Start something"
- Questions about non-currency topics
- Incomplete or ambiguous statements without currency context
- Any phrase that doesn't explicitly mention or imply a specific currency
- Nonsensical or testing inputs

ABSOLUTE REQUIREMENTS:
- The input MUST explicitly reference a currency, country's money, or exchange rates
- Never interpret non-currency phrases as currency requests
- Never default to any currency (including USD) for unclear inputs
- Never guess what currency someone might want based on non-currency context
- If the input doesn't clearly mention money/currency/exchange rates, REJECT IT

Available currencies: {", ".join(CURRENCIES)}

If the input explicitly mentions a currency and you can confidently identify it, use the get_exchange_rates tool.
If the input does NOT explicitly reference currencies or exchange rates, respond with "UNKNOWN_CURRENCY" and do not call any tools.
""".strip()

    try:
        response = await gpt4o_mini_agent.ainvoke(
            {"messages": [{"role": "user", "content": currency_and_rates_prompt}]}
        )
    except Exception as e:
        return ForeignExchangeGraphCommand(
            update=state.set_failure_message(
                f"Error processing currency request: {str(e)}"
            ),
            goto="failure_node",
        )

    messages = response["messages"]
    tool_call = messages[1]
    if not tool_call.tool_calls:
        return ForeignExchangeGraphCommand(
            update=state.set_failure_message(
                f"Could not identify a valid currency from: '{state.raw_user_input}'"
            ),
            goto="failure_node",
        )

    base_currency = tool_call.tool_calls[0]["args"]["base_currency"]
    if base_currency not in CURRENCIES:
        return ForeignExchangeGraphCommand(
            update=state.set_failure_message(
                f"AI identified invalid currency: '{base_currency}'"
            ),
            goto="failure_node",
        )

    return ForeignExchangeGraphCommand(
        update=state.set_user_currency_input(cast(Currencies, base_currency)).set_rates(
            json.loads(messages[2].content)
        ),
        goto="end_node",
    )


def end_node(state: ForeignExchangeGraphState) -> ForeignExchangeGraphState:
    return state


foreign_exchange_graph = (
    StateGraph(ForeignExchangeGraphState)
    .add_node("get_user_currency_input_node", get_user_currency_input_node)
    .add_node("failure_node", failure_node)
    .add_node(
        "determine_currency_and_get_rates_node", determine_currency_and_get_rates_node
    )
    .add_node("end_node", end_node)
    .set_entry_point("get_user_currency_input_node")
    .set_finish_point("failure_node")
    .set_finish_point("end_node")
    .compile()
)

foreign_exchange_initial_state = ForeignExchangeGraphState(
    raw_user_input=None,
    user_currency_input=None,
    failure_message=None,
    rates={},
)


async def foreign_exchange_graph_async_invoke() -> ForeignExchangeGraphState:
    end_state = await foreign_exchange_graph.ainvoke(
        input=foreign_exchange_initial_state  # type: ignore
    )

    return ForeignExchangeGraphState(**end_state)

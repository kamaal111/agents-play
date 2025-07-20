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
from foreign_exchange.prompts import determine_currency_prompt

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

    currency_and_rates_prompt = determine_currency_prompt(
        user_input=state.raw_user_input
    )

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


async def foreign_exchange_rate_invoke(request: str) -> ForeignExchangeGraphState:
    foreign_exchange_initial_state = ForeignExchangeGraphState(
        raw_user_input=request,
        user_currency_input=None,
        failure_message=None,
        rates={},
    )
    end_state = await foreign_exchange_graph.ainvoke(
        input=foreign_exchange_initial_state  # type: ignore
    )

    return ForeignExchangeGraphState(**end_state)

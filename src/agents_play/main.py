import asyncio
from typing import Literal, Self, cast

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from langgraph.types import Command as LanggraphCommand
from pydantic import BaseModel

from agents_play.conf import settings
from foreign_exchange.client import ForeignExchangeClient
from foreign_exchange.currencies import (
    CURRENCIES,
    CURRENCIES_MAPPED_TO_NAMES,
    Currencies,
)

assert settings.openai_api_key


GraphNodes = Literal[
    "get_user_currency_input_node",
    "identify_currency_code_node",
    "end_node",
    "failure_node",
    "get_foreign_exchange_rates",
]

Command = LanggraphCommand[GraphNodes]


class GraphState(BaseModel):
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


gpt4o_mini_model = init_chat_model("gpt-4o-mini", model_provider="openai")

foreign_exchange_client = ForeignExchangeClient()


def get_user_currency_input_node(state: GraphState) -> Command:
    user_currency_input: str | None = None
    try:
        user_currency_input = input(
            "Which currency do you want to know the rates of today?\n"
        ).strip()
    except Exception:
        pass

    if not user_currency_input:
        return Command(
            update=state.set_failure_message("Invalid user input"), goto="failure_node"
        )

    return Command(
        update=state.set_raw_user_input(user_currency_input),
        goto="identify_currency_code_node",
    )


def failure_node(state: GraphState) -> GraphState:
    assert state.failure_message

    print(state.failure_message)

    return state


def identify_currency_code_node(state: GraphState) -> Command:
    assert state.raw_user_input

    identify_currency_code_prompt = f"""
You are a currency identification assistant. Based on the user's input, determine which currency they are referring to.

Available currencies and their symbols:
{"\n".join([f"- {symbol}: {name}" for symbol, name in CURRENCIES_MAPPED_TO_NAMES.items()])}

User input: "{state.raw_user_input}"

Please respond with ONLY the 3-letter currency symbol (e.g., "USD", "EUR", "GBP") that best matches the user's input.
If the user mentions a currency name, country, or partial match, return the corresponding symbol.
If you cannot determine a clear match, respond with "UNKNOWN".

Currency symbol:
""".strip()
    gpt4o_mini_model_message = gpt4o_mini_model.invoke(identify_currency_code_prompt)
    assert isinstance(gpt4o_mini_model_message.content, str)

    identified_currency_code = gpt4o_mini_model_message.content.strip().upper()
    if identified_currency_code not in CURRENCIES:
        return Command(
            update=state.set_failure_message(
                f"'{state.raw_user_input}' is an unknown forex"
            ),
            goto="failure_node",
        )

    # Validated above so its safe to cast
    identified_currency_code = cast(Currencies, identified_currency_code)

    return Command(
        update=state.set_user_currency_input(identified_currency_code),
        goto="get_foreign_exchange_rates",
    )


async def get_foreign_exchange_rates(state: GraphState) -> Command:
    assert state.user_currency_input

    try:
        response = await foreign_exchange_client.get_rates(
            base=state.user_currency_input
        )
    except Exception:
        return Command(
            update=state.set_failure_message(
                f"Failed to get exchange rates for '{state.user_currency_input}'"
            ),
            goto="failure_node",
        )

    return Command(update=state.set_rates(response.rates), goto="end_node")


def end_node(state: GraphState) -> GraphState:
    return state


graph = (
    StateGraph(GraphState)
    .add_node("get_user_currency_input_node", get_user_currency_input_node)
    .add_node("failure_node", failure_node)
    .add_node("identify_currency_code_node", identify_currency_code_node)
    .add_node("get_foreign_exchange_rates", get_foreign_exchange_rates)
    .add_node("end_node", end_node)
    .set_entry_point("get_user_currency_input_node")
    .set_finish_point("failure_node")
    .set_finish_point("end_node")
    .compile()
)

initial_state = GraphState(
    raw_user_input=None,
    user_currency_input=None,
    failure_message=None,
    rates={},
)


async def main() -> None:
    end_state = await graph.ainvoke(input=initial_state)  # type: ignore
    print(GraphState(**end_state))


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from typing import Literal, cast

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from pydantic import BaseModel

from agents_play.conf import settings
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
]


class GraphState(BaseModel):
    raw_user_input: str | None
    user_currency_input: Currencies | None
    failure_message: str | None
    next_node: GraphNodes | None


gpt4o_mini_model = init_chat_model("gpt-4o-mini", model_provider="openai")


def get_user_currency_input_node(state: GraphState) -> GraphState:
    user_currency_input: str | None = None
    try:
        user_currency_input = input(
            "Which currency do you want to know the rates of today?\n"
        ).strip()
    except Exception:
        pass

    if not user_currency_input:
        return GraphState(
            raw_user_input=state.raw_user_input,
            user_currency_input=state.user_currency_input,
            failure_message="Invalid user input",
            next_node="failure_node",
        )

    return GraphState(
        raw_user_input=user_currency_input,
        user_currency_input=state.user_currency_input,
        failure_message=state.failure_message,
        next_node="identify_currency_code_node",
    )


def failure_node(state: GraphState) -> GraphState:
    assert state.failure_message

    print(state.failure_message)

    return state


def identify_currency_code_node(state: GraphState) -> GraphState:
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
        return GraphState(
            raw_user_input=state.raw_user_input,
            user_currency_input=state.user_currency_input,
            failure_message=f"'{state.raw_user_input}' is an unknown forex",
            next_node="failure_node",
        )

    # Validated above so its safe to cast
    identified_currency_code = cast(Currencies, identified_currency_code)

    return GraphState(
        raw_user_input=state.raw_user_input,
        user_currency_input=identified_currency_code,
        failure_message=state.failure_message,
        next_node="end_node",
    )


def end_node(state: GraphState) -> GraphState:
    return state


def next_node_edge(state: GraphState) -> GraphNodes:
    assert state.next_node

    return state.next_node


graph = (
    StateGraph(GraphState)
    .add_node("get_user_currency_input_node", get_user_currency_input_node)
    .add_node("failure_node", failure_node)
    .add_node("identify_currency_code_node", identify_currency_code_node)
    .add_node("end_node", end_node)
    .set_entry_point("get_user_currency_input_node")
    .add_conditional_edges("get_user_currency_input_node", next_node_edge)
    .add_conditional_edges("identify_currency_code_node", next_node_edge)
    .set_finish_point("failure_node")
    .set_finish_point("end_node")
    .compile()
)

initial_state = GraphState(
    raw_user_input=None, user_currency_input=None, failure_message=None, next_node=None
)


async def main() -> None:
    end_state = await graph.ainvoke(input=initial_state)  # type: ignore
    print(GraphState(**end_state))


if __name__ == "__main__":
    asyncio.run(main())

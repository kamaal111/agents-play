from typing import Literal, cast

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from agents_play.conf import settings
from foreign_exchange.currencies import (
    CURRENCIES,
    CURRENCIES_MAPPED_TO_NAMES,
    Currencies,
)

assert settings.openai_api_key


class GraphState(BaseModel):
    raw_user_input: str | None = None
    user_currency_input: Currencies | None = None


graph_builder = StateGraph(GraphState)

gpt4o_mini_model = init_chat_model("gpt-4o-mini", model_provider="openai")


def identify_currency_code_node(state: GraphState) -> GraphState:
    user_currency_input = input(
        "Which currency do you want to know the rates of today?\n"
    )
    identify_currency_code_prompt = f"""
You are a currency identification assistant. Based on the user's input, determine which currency they are referring to.

Available currencies and their symbols:
{"\n".join([f"- {symbol}: {name}" for symbol, name in CURRENCIES_MAPPED_TO_NAMES.items()])}

User input: "{user_currency_input}"

Please respond with ONLY the 3-letter currency symbol (e.g., "USD", "EUR", "GBP") that best matches the user's input.
If the user mentions a currency name, country, or partial match, return the corresponding symbol.
If you cannot determine a clear match, respond with "UNKNOWN".

Currency symbol:
""".strip()
    gpt4o_mini_model_message = gpt4o_mini_model.invoke(identify_currency_code_prompt)
    assert isinstance(gpt4o_mini_model_message.content, str)

    identified_currency_code = gpt4o_mini_model_message.content.strip().upper()
    if identified_currency_code not in CURRENCIES:
        return GraphState(raw_user_input=user_currency_input)

    # Validated above so its safe to cast
    identified_currency_code = cast(Currencies, identified_currency_code)

    return GraphState(
        raw_user_input=user_currency_input, user_currency_input=identified_currency_code
    )


def unknown_currency_code_node(state: GraphState) -> GraphState:
    print(f"'{state.raw_user_input or ''}' is an unknown forex")

    return state


def end_node(state: GraphState) -> GraphState:
    return state


def identify_currency_code_decision_edge(
    state: GraphState,
) -> Literal["end_node", "unknown_currency_code_node"]:
    if state.user_currency_input is None:
        return "unknown_currency_code_node"

    return "end_node"


graph_builder.add_node("identify_currency_code_node", identify_currency_code_node)
graph_builder.add_node("unknown_currency_code_node", unknown_currency_code_node)
graph_builder.add_node("end_node", end_node)

graph_builder.add_edge(START, "identify_currency_code_node")
graph_builder.add_conditional_edges(
    "identify_currency_code_node", identify_currency_code_decision_edge
)
graph_builder.add_edge("unknown_currency_code_node", END)
graph_builder.add_edge("end_node", END)

graph = graph_builder.compile()

initial_state = GraphState()
end_state = graph.invoke(input=initial_state)  # type: ignore
print(GraphState(**end_state))

from functools import reduce
from typing import Any, Literal

from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command as LanggraphCommand
from pydantic import BaseModel

from llm.conf import settings
from llm.schemas import ChatRoomMessage

assert settings.openai_api_key

LLMGraphNodes = Literal[
    "llm_entry_node",
    "llm_finish_node",
]

LLMExchangeGraphCommand = LanggraphCommand[LLMGraphNodes]


LLMExceptionCodes = Literal["unsupported_llm", "agent_invocation_failed"]


class LLMGraphStateFailure(BaseModel):
    def __init__(self, code: LLMExceptionCodes, cause: Exception | None = None):
        self.code = code
        self.cause = cause


class LLMGraphStateSuccess(BaseModel):
    ai_response: AIMessage


class LLMGraphState(BaseModel):
    question: ChatRoomMessage
    messages: list[ChatRoomMessage]
    result: LLMGraphStateSuccess | LLMGraphStateFailure | None

    def with_error_result(self, error_result: LLMGraphStateFailure) -> "LLMGraphState":
        assert self.result is None

        self.result = error_result

        return self

    def with_success_result(
        self, success_result: LLMGraphStateSuccess
    ) -> "LLMGraphState":
        assert self.result is None

        self.result = success_result

        return self

    @property
    def ok_result(self) -> LLMGraphStateSuccess | None:
        assert self.result is not None

        if not self.is_ok:
            return None

        assert isinstance(self.result, LLMGraphStateSuccess)

        return self.result

    @property
    def is_ok(self) -> bool:
        assert self.result is not None

        return isinstance(self.result, LLMGraphStateSuccess)


LLM_AGENTS: dict[str, CompiledStateGraph[Any]] = reduce(
    lambda acc, name: {**acc, name: create_react_agent(name, tools=[])},
    {"openai:gpt-4o-mini"},
    {},
)


async def llm_entry_node(state: LLMGraphState) -> LLMExchangeGraphCommand:
    agent = LLM_AGENTS.get(state.question.agent_name)
    if agent is None:
        return LLMExchangeGraphCommand(
            update=state.with_error_result(
                LLMGraphStateFailure(code="unsupported_llm")
            ),
            goto="llm_finish_node",
        )

    input_messages = list(
        map(
            lambda message: message.model_dump(mode="json"),
            state.messages + [state.question.as_llm_message],
        )
    )

    try:
        response = await agent.ainvoke({"messages": input_messages})
    except Exception as e:
        return LLMExchangeGraphCommand(
            update=state.with_error_result(
                LLMGraphStateFailure(code="agent_invocation_failed", cause=e)
            ),
            goto="llm_finish_node",
        )

    messages = response["messages"]
    ai_message = messages[1]

    assert isinstance(ai_message, AIMessage)

    return LLMExchangeGraphCommand(
        update=state.with_success_result(LLMGraphStateSuccess(ai_response=ai_message)),
        goto="llm_finish_node",
    )


def llm_finish_node(state: LLMGraphState) -> LLMGraphState:
    assert state.result is not None

    return state


llm_graph = (
    StateGraph(LLMGraphState)
    .add_node("llm_entry_node", llm_entry_node)
    .add_node("llm_finish_node", llm_finish_node)
    .set_entry_point("llm_entry_node")
    .set_finish_point("llm_finish_node")
    .compile()
)


async def llm_graph_invoke_question(
    question: ChatRoomMessage, messages: list[ChatRoomMessage]
) -> LLMGraphState:
    state = LLMGraphState(question=question, messages=messages, result=None)
    end_state = await llm_graph.ainvoke(
        input=state  # type: ignore
    )
    validated_end_state = LLMGraphState(**end_state)

    assert validated_end_state.result is not None

    return validated_end_state

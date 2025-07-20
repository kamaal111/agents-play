from functools import reduce
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command as LanggraphCommand
from pydantic import BaseModel
from todos.graph import todos_graph_invoke

from llm.conf import settings
from llm.schemas import ChatRoomMessage
from llm.tools import get_exchange_rates_tool

if TYPE_CHECKING:
    from database.database import Databaseable

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


class LLMGraphConfig(TypedDict):
    database: "Databaseable"


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


LLM_AGENTS_SYSTEM_PROMPT = """
You are a helpful AI assistant that can help users with various tasks. You have access to a foreign exchange rates tool that can provide current currency exchange rates.

IMPORTANT: Only use the get_exchange_rates tool when the user specifically asks about:
- Currency exchange rates
- Converting between currencies
- Current foreign exchange information
- Currency values or comparisons

DO NOT use the get_exchange_rates tool for:
- General questions unrelated to currencies
- Mathematical calculations that don't involve currency conversion
- Other topics not related to foreign exchange

When the user asks about exchange rates or currency conversion, use the get_exchange_rates tool with their exact request to get the most current and accurate information.

For all other questions, respond normally without using any tools.
""".strip()

LLM_AGENTS: dict[str, CompiledStateGraph[Any]] = reduce(
    lambda acc, name: {
        **acc,
        name: create_react_agent(
            name, tools=[get_exchange_rates_tool], prompt=LLM_AGENTS_SYSTEM_PROMPT
        ),
    },
    {"openai:gpt-4o-mini"},
    {},
)

PLANNING_AGENT_PROMPT = """
You are a routing planning agent. Your job is to analyze user input and determine which type of service they need.

Based on the user's input, you must respond with exactly ONE of these words:
- "todo" - if the user wants to do anything related to todos/tasks (create, add, list, show, view todos)
- "general" - for everything else including exchange rates, currency conversion, general questions, or any non-todo related requests

Examples:
- "Add a new task to buy groceries" → todo
- "I need to create a reminder to call mom" → todo
- "Show me my todos" → todo
- "What tasks do I have?" → todo
- "List all my todo items" → todo
- "Get me exchange rates for USD to EUR" → general
- "What's the weather like?" → general
- "Convert 100 USD to JPY" → general
- "Help me with my homework" → general
- "How are currency rates today?" → general

Only respond with the single word: todo or general. Do not provide any explanation or additional text.
""".strip()

planning_agent = create_react_agent(
    "openai:gpt-4o-mini", tools=[], prompt=PLANNING_AGENT_PROMPT
)


async def llm_entry_node(
    state: LLMGraphState, config: RunnableConfig
) -> LLMExchangeGraphCommand:
    try:
        planning_response = await planning_agent.ainvoke(
            {"messages": [state.question.as_llm_message.model_dump(mode="json")]}
        )
    except Exception as e:
        return LLMExchangeGraphCommand(
            update=state.with_error_result(
                LLMGraphStateFailure(code="agent_invocation_failed", cause=e)
            ),
            goto="llm_finish_node",
        )

    planning_messages = planning_response["messages"]
    planning_ai_message = planning_messages[-1]

    assert isinstance(planning_ai_message, AIMessage)
    assert isinstance(planning_ai_message.content, str)

    agent = LLM_AGENTS.get(state.question.agent_name)
    if agent is None:
        return LLMExchangeGraphCommand(
            update=state.with_error_result(
                LLMGraphStateFailure(code="unsupported_llm")
            ),
            goto="llm_finish_node",
        )

    if planning_ai_message.content == "todo":
        configurable: LLMGraphConfig = config["configurable"]  # type: ignore
        todo_result = await todos_graph_invoke(
            database=configurable["database"], user_input=state.question.content
        )

        if todo_result.is_ok:
            todo_ok_result = todo_result.ok_result
            assert todo_ok_result is not None

            if todo_ok_result.action == "create":
                if todo_result.new_todo:
                    summary_prompt = f"The user asked: '{state.question.content}'. I successfully created a new todo item with the title '{todo_result.new_todo.title}'. Please provide a helpful response confirming the todo was created."
                else:
                    summary_prompt = f"The user asked: '{state.question.content}'. I determined this was a todo creation request, but no todo was actually created. Please explain this to the user."
            elif todo_ok_result.action == "list":
                if todo_result.todos:
                    todos_list = "\n".join(
                        [f"- {todo.title}" for todo in todo_result.todos]
                    )
                    summary_prompt = f"The user asked: '{state.question.content}'. Here are their current todos:\n{todos_list}\n\nPlease provide a helpful response showing them their todo list."
                else:
                    summary_prompt = f"The user asked: '{state.question.content}'. They currently have no todos in their list. Please let them know their todo list is empty."
            else:
                summary_prompt = f"The user asked: '{state.question.content}'. I determined this was a todo-related request but the action '{todo_ok_result.action}' is not supported. Please explain this to the user."

            summary_messages = [{"role": "user", "content": summary_prompt}]

            try:
                summary_response = await agent.ainvoke({"messages": summary_messages})
            except Exception as e:
                return LLMExchangeGraphCommand(
                    update=state.with_error_result(
                        LLMGraphStateFailure(code="agent_invocation_failed", cause=e)
                    ),
                    goto="llm_finish_node",
                )

            summary_ai_message = summary_response["messages"][-1]

            assert isinstance(summary_ai_message, AIMessage)

            return LLMExchangeGraphCommand(
                update=state.with_success_result(
                    LLMGraphStateSuccess(ai_response=summary_ai_message)
                ),
                goto="llm_finish_node",
            )
        else:
            # Failed to perform todo action, let's pass through and try something else
            pass

    # Handle general case
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
    ai_message = messages[-1]

    assert isinstance(ai_message, AIMessage)

    return LLMExchangeGraphCommand(
        update=state.with_success_result(LLMGraphStateSuccess(ai_response=ai_message)),
        goto="llm_finish_node",
    )


def llm_finish_node(state: LLMGraphState) -> LLMGraphState:
    assert state.result is not None

    return state


llm_graph = (
    StateGraph(LLMGraphState, config_schema=LLMGraphConfig)
    .add_node("llm_entry_node", llm_entry_node)
    .add_node("llm_finish_node", llm_finish_node)
    .set_entry_point("llm_entry_node")
    .set_finish_point("llm_finish_node")
    .compile()
)


async def llm_graph_invoke_question(
    database: "Databaseable", question: ChatRoomMessage, messages: list[ChatRoomMessage]
) -> LLMGraphState:
    state = LLMGraphState(question=question, messages=messages, result=None)
    config = {"configurable": {"database": database}}
    end_state = await llm_graph.ainvoke(
        input=state,  # type: ignore
        config=config,  # type: ignore
    )
    validated_end_state = LLMGraphState(**end_state)

    assert validated_end_state.result is not None

    return validated_end_state

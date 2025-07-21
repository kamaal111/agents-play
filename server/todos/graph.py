from typing import TYPE_CHECKING, Literal, TypedDict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command as LanggraphCommand
from pydantic import BaseModel
from sqlmodel import Session

from todos.conf import settings
from todos.models import Todo, TodoDataclass
from todos.schemas import TodoCreatePayload

if TYPE_CHECKING:
    from database.database import Databaseable

assert settings.openai_api_key

TodosGraphNodes = Literal[
    "todos_entry_node",
    "todos_create_node",
    "todos_list_node",
    "todos_finish_node",
]

TodosGraphCommand = LanggraphCommand[TodosGraphNodes]


class TodosGraphConfig(TypedDict):
    database: "Databaseable"


TodosExceptionCodes = Literal["agent_invocation_failed"]


class TodosGraphStateFailure(BaseModel):
    def __init__(self, code: TodosExceptionCodes, cause: Exception | None = None):
        self.code = code
        self.cause = cause


TodosActionTaken = Literal["create", "list", "unknown"]


class TodosGraphStateSuccess(BaseModel):
    action: TodosActionTaken


class TodosGraphState(BaseModel):
    user_input: str
    action: TodosActionTaken | None
    result: TodosGraphStateSuccess | TodosGraphStateFailure | None
    todos: list[TodoDataclass]
    new_todo: TodoDataclass | None

    def with_error_result(
        self, error_result: TodosGraphStateFailure
    ) -> "TodosGraphState":
        assert self.result is None

        self.result = error_result

        return self

    def with_success_result(
        self, success_result: TodosGraphStateSuccess
    ) -> "TodosGraphState":
        assert self.result is None

        self.result = success_result

        return self

    def with_action(self, action: TodosActionTaken) -> "TodosGraphState":
        self.action = action

        return self

    def with_new_todo(self, new_todo: TodoDataclass) -> "TodosGraphState":
        assert self.action == "create"

        self.new_todo = new_todo

        return self

    def with_todos(self, todos: list[TodoDataclass]) -> "TodosGraphState":
        assert self.action == "list"

        self.todos = todos

        return self

    @property
    def ok_result(self) -> TodosGraphStateSuccess | None:
        assert self.result is not None

        if not self.is_ok:
            return None

        assert isinstance(self.result, TodosGraphStateSuccess)

        return self.result

    @property
    def is_ok(self) -> bool:
        assert self.result is not None

        return isinstance(self.result, TodosGraphStateSuccess)


PLANNING_AGENT_PROMPT = """
You are a TODO management planning agent. Your job is to analyze user input and determine what action they want to take with their todos.

Based on the user's input, you must respond with exactly ONE of these words:
- "create" - if the user wants to add, create, make, or insert a new todo item
- "list" - if the user wants to see, show, display, view, or get their existing todos
- "unknown" - if the user's request doesn't match either of the above actions

Examples:
- "Add a new task to buy groceries" → create
- "I need to create a reminder to call mom" → create
- "Show me my todos" → list
- "What tasks do I have?" → list
- "List all my todo items" → list
- "Delete my first todo" → unknown
- "What's the weather like?" → unknown

Only respond with the single word: create, list, or unknown. Do not provide any explanation or additional text.
""".strip()


planning_agent = create_react_agent(
    "openai:gpt-4o-mini", tools=[], prompt=PLANNING_AGENT_PROMPT
)


TITLE_EXTRACTING_AGENT_PROMPT = """
You are a TODO title extraction agent. Your job is to analyze user input and extract a clear, concise title for their todo item.

Based on the user's input, extract the main task or action they want to accomplish and format it as a clean todo title.

Guidelines:
- Keep titles concise but descriptive (ideally 2-8 words)
- Use action words when possible (Buy, Call, Complete, etc.)
- Remove unnecessary words like "I need to", "I want to", "Can you help me", etc.
- Capitalize the first word
- Don't include punctuation at the end
- Focus on the core action or task

Examples:
- "I need to buy groceries for dinner tonight" → "Buy groceries for dinner"
- "Add a task to call my mom tomorrow" → "Call mom"
- "I want to create a reminder to finish my homework" → "Finish homework"
- "Help me remember to schedule a doctor appointment" → "Schedule doctor appointment"
- "I should clean my room this weekend" → "Clean room"
- "Add pay bills to my todo list" → "Pay bills"
- "Create a task for walking the dog" → "Walk the dog"

Only respond with the extracted title. Do not provide any explanation or additional text.
""".strip()

title_extracting_agent = create_react_agent(
    "openai:gpt-4o-mini", tools=[], prompt=TITLE_EXTRACTING_AGENT_PROMPT
)


async def todos_entry_node(state: TodosGraphState) -> TodosGraphCommand:
    messages = [{"role": "user", "content": state.user_input}]
    try:
        planning_response = await planning_agent.ainvoke({"messages": messages})
    except Exception as e:
        return TodosGraphCommand(
            update=state.with_error_result(
                TodosGraphStateFailure(code="agent_invocation_failed", cause=e)
            )
        )

    messages = planning_response["messages"]
    ai_message = messages[-1]

    assert isinstance(ai_message, AIMessage)
    assert isinstance(ai_message.content, str)

    if ai_message.content == "create":
        return TodosGraphCommand(
            update=state.with_action("create"), goto="todos_create_node"
        )
    elif ai_message.content == "list":
        return TodosGraphCommand(
            update=state.with_action("list"), goto="todos_list_node"
        )

    return TodosGraphCommand(
        update=state.with_success_result(TodosGraphStateSuccess(action="unknown")),
        goto="todos_finish_node",
    )


async def todos_create_node(
    state: TodosGraphState, config: RunnableConfig
) -> TodosGraphCommand:
    messages = [{"role": "user", "content": state.user_input}]
    try:
        title_response = await title_extracting_agent.ainvoke({"messages": messages})
    except Exception as e:
        return TodosGraphCommand(
            update=state.with_error_result(
                TodosGraphStateFailure(code="agent_invocation_failed", cause=e)
            ),
            goto="todos_finish_node",
        )

    title_messages = title_response["messages"]
    title_ai_message = title_messages[-1]

    assert isinstance(title_ai_message, AIMessage)
    assert isinstance(title_ai_message.content, str)

    todo_title = title_ai_message.content.strip()

    configurable: TodosGraphConfig = config["configurable"]  # type: ignore
    database = configurable["database"]

    new_todo: TodoDataclass
    with Session(database.engine) as session:
        new_todo = Todo.create(
            payload=TodoCreatePayload(title=todo_title), session=session
        )

    return TodosGraphCommand(
        update=state.with_success_result(
            TodosGraphStateSuccess(action="create")
        ).with_new_todo(new_todo=new_todo),
        goto="todos_finish_node",
    )


def todos_list_node(
    state: TodosGraphState, config: RunnableConfig
) -> TodosGraphCommand:
    configurable: TodosGraphConfig = config["configurable"]  # type: ignore
    database = configurable["database"]

    with Session(database.engine) as session:
        todos = Todo.list(session=session)

    return TodosGraphCommand(
        update=state.with_success_result(
            TodosGraphStateSuccess(action="list")
        ).with_todos(todos),
        goto="todos_finish_node",
    )


def todos_finish_node(state: TodosGraphState) -> TodosGraphState:
    return state


todos_graph = (
    StateGraph(TodosGraphState, config_schema=TodosGraphConfig)
    .add_node("todos_entry_node", todos_entry_node)
    .add_node("todos_create_node", todos_create_node)
    .add_node("todos_list_node", todos_list_node)
    .add_node("todos_finish_node", todos_finish_node)
    .set_entry_point("todos_entry_node")
    .set_finish_point("todos_finish_node")
    .compile()
)


async def todos_graph_invoke(
    database: "Databaseable", user_input: str
) -> TodosGraphState:
    state = TodosGraphState(
        user_input=user_input, action="unknown", result=None, todos=[], new_todo=None
    )
    config = {"configurable": {"database": database}}
    end_state = await todos_graph.ainvoke(
        input=state,  # type: ignore
        config=config,  # type: ignore
    )
    validated_end_state = TodosGraphState(**end_state)

    assert validated_end_state.result is not None

    return validated_end_state

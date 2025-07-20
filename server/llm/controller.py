import uuid
from typing import Annotated, Protocol

from common.datetime_utils import datetime_now_with_timezone
from common.exceptions import AgentsPlayGeneralError
from database.database import Databaseable, get_database
from fastapi import Depends
from sqlmodel import Session

from llm.graph import llm_graph_invoke_question
from llm.models import ChatRoom
from llm.schemas import (
    ChatRoomMessage,
    CreateChatMessagePayload,
    CreateChatMessageResponse,
    CreateChatRoomPayload,
    ListChatMessagesResponse,
)

LLM_PROVIDER = "openai"
LLM_KEY = "gpt-4o-mini"


class LLMControllable(Protocol):
    database: Databaseable

    def list_chat_messages(self) -> ListChatMessagesResponse: ...

    async def create_chat_message(
        self, payload: CreateChatMessagePayload
    ) -> CreateChatMessageResponse: ...


class LLMController(LLMControllable):
    database: Databaseable

    def __init__(self, database: Databaseable):
        self.database = database

    def list_chat_messages(self) -> ListChatMessagesResponse:
        messages: list[ChatRoomMessage]
        with Session(self.database.engine) as session:
            rooms = ChatRoom.list(session=session)
            if len(rooms) == 0:
                return ListChatMessagesResponse(detail="OK", data=[])

            room = rooms[0]
            messages = room.validated_messages()

        return ListChatMessagesResponse(detail="OK", data=messages)

    async def create_chat_message(self, payload) -> CreateChatMessageResponse:
        request_time = datetime_now_with_timezone()
        messages: list[ChatRoomMessage] = []
        existing_room: ChatRoom | None = None
        with Session(self.database.engine) as session:
            rooms = ChatRoom.list(session=session)
            if len(rooms) > 0:
                room = rooms[0]
                existing_room = room
                messages = room.validated_messages()

        question = ChatRoomMessage(
            id=uuid.uuid4(),
            role="user",
            content=payload.message,
            llm_provider=LLM_PROVIDER,
            llm_key=LLM_KEY,
            date=request_time,
        )
        end_state = await llm_graph_invoke_question(
            database=self.database, question=question, messages=messages
        )
        response_time = datetime_now_with_timezone()
        if not end_state.is_ok:
            raise AgentsPlayGeneralError

        graph_ok_result = end_state.ok_result
        assert graph_ok_result is not None

        ai_response = graph_ok_result.ai_response

        assert isinstance(ai_response.content, str)

        response = ChatRoomMessage(
            role="assistant",
            content=ai_response.content,
            id=uuid.uuid4(),
            llm_provider=LLM_PROVIDER,
            llm_key=LLM_KEY,
            date=response_time,
        )
        with Session(self.database.engine) as session:
            if existing_room is not None:
                room = existing_room.add_messages(
                    messages=[question, response], session=session
                )
            else:
                room = ChatRoom.create(
                    payload=CreateChatRoomPayload(
                        question=question,
                        answer=response,
                    ),
                    session=session,
                )

            return CreateChatMessageResponse(
                role=response.role,
                content=response.content,
                id=response.id,
                llm_provider=response.llm_provider,
                llm_key=response.llm_key,
                date=response.date,
                detail="Created",
                room_id=room.id,
                title=room.title,
                updated_at=room.updated_at,
            )


def get_llm_controller(
    database: Annotated[Databaseable, Depends(get_database)],
) -> LLMControllable:
    return LLMController(database)

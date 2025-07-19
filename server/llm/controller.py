from typing import Annotated, Protocol

from database.database import Databaseable, get_database
from fastapi import Depends
from sqlmodel import Session

from llm.models import ChatRoom
from llm.schemas import ListChatMessagesResponse


class LLMControllable(Protocol):
    database: Databaseable

    def list_chat_messages(self) -> ListChatMessagesResponse: ...


class LLMController(LLMControllable):
    database: Databaseable

    def __init__(self, database: Databaseable):
        self.database = database

    def list_chat_messages(self) -> ListChatMessagesResponse:
        with Session(self.database.engine) as session:
            rooms = ChatRoom.list(session=session)

            if len(rooms) == 0:
                return ListChatMessagesResponse(detail="OK", data=[])

            room = rooms[0]
            messages = room.validated_messages()

            return ListChatMessagesResponse(detail="OK", data=messages)


def get_llm_controller(
    database: Annotated[Databaseable, Depends(get_database)],
) -> LLMControllable:
    return LLMController(database)

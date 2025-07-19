from datetime import datetime
from typing import Literal

from common.schemas import OKResponse
from pydantic import BaseModel

AssistantMessageRole = Literal["assistant"]
MessageRoles = Literal["user"] | AssistantMessageRole


class LLMMessage(BaseModel):
    role: MessageRoles
    content: str


class ChatRoomMessage(LLMMessage):
    llm_provider: str
    llm_key: str
    date: datetime

    @property
    def as_llm_message(self) -> LLMMessage:
        return LLMMessage(role=self.role, content=self.content)


class CreateChatRoomPayload(BaseModel):
    question: ChatRoomMessage
    answer: ChatRoomMessage


class ListChatMessagesResponse(OKResponse):
    data: list[ChatRoomMessage]

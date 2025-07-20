import uuid
from datetime import datetime
from typing import Literal

from common.schemas import CreatedResponse, OKResponse
from pydantic import BaseModel, Field, field_validator

AssistantMessageRole = Literal["assistant"]
MessageRoles = Literal["user"] | AssistantMessageRole


class LLMMessage(BaseModel):
    role: MessageRoles
    content: str


class ChatRoomMessage(LLMMessage):
    id: uuid.UUID
    llm_provider: str
    llm_key: str
    date: datetime

    @property
    def agent_name(self) -> str:
        return f"{self.llm_provider}:{self.llm_key}"

    @property
    def as_llm_message(self) -> LLMMessage:
        return LLMMessage(role=self.role, content=self.content)


class CreateChatMessagePayload(BaseModel):
    message: str = Field(..., min_length=1)

    @field_validator("message", mode="before")
    @classmethod
    def strip_whitespaces(cls, v: str) -> str:
        return v.strip()


class CreateChatRoomPayload(BaseModel):
    question: ChatRoomMessage
    answer: ChatRoomMessage


class CreateChatMessageResponse(CreatedResponse, ChatRoomMessage):
    room_id: uuid.UUID
    title: str
    updated_at: datetime


class ListChatMessagesResponse(OKResponse):
    data: list[ChatRoomMessage]

import uuid
from datetime import datetime
from typing import Any, Sequence

from common.datetime_utils import datetime_now_with_timezone
from common.exceptions import AgentsPlayBadRequestError
from sqlalchemy import ARRAY, JSON, Column, DateTime
from sqlmodel import Field, SQLModel, Session, col, select

from llm.schemas import ChatRoomMessage, CreateChatRoomPayload

CHAT_ROOM_MAX_TITLE_LENGTH = 255


class ChatRoom(SQLModel, table=True):
    __tablename__: str = "chat_room"  # type: ignore

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            onupdate=datetime_now_with_timezone,
        ),
        default_factory=datetime_now_with_timezone,
    )
    title: str = Field(min_length=1)
    messages: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(ARRAY(JSON), nullable=False)
    )

    def validated_messages(self) -> list[ChatRoomMessage]:
        return sorted(
            map(lambda message: ChatRoomMessage(**message), self.messages),
            key=lambda message: message.date,
            reverse=False,
        )

    def add_messages(
        self, messages: list[ChatRoomMessage], session: Session
    ) -> "ChatRoom":
        all_messages = self.validated_messages()
        all_messages.extend(messages)
        self.messages = list(
            map(lambda message: message.model_dump(mode="json"), all_messages)
        )

        session.add(self)
        session.commit()

        room = self
        session.refresh(room)

        return room

    @staticmethod
    def list(session: Session) -> Sequence["ChatRoom"]:
        query = select(ChatRoom).order_by(col(ChatRoom.updated_at).desc())

        return session.exec(query).all()

    @staticmethod
    def create(
        payload: CreateChatRoomPayload, session: Session, commit: bool = True
    ) -> "ChatRoom":
        if len(payload.question.content.strip()) == 0:
            raise AgentsPlayBadRequestError

        messages = [
            payload.question.model_dump(mode="json"),
            payload.answer.model_dump(mode="json"),
        ]

        room = ChatRoom(
            title=payload.question.content.strip()[:CHAT_ROOM_MAX_TITLE_LENGTH],
            messages=messages,
        )

        session.add(room)
        if commit:
            session.commit()

        return room

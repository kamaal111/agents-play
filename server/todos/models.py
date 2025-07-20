import uuid
from datetime import datetime

from common.datetime_utils import datetime_now_with_timezone
from sqlmodel import Column, DateTime, Field, SQLModel, Session

from todos.schemas import TodoCreatePayload


class Todo(SQLModel, table=True):
    __tablename__: str = "todo"  # type: ignore

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
    completed: bool = Field(default=False)

    @staticmethod
    def create(
        payload: TodoCreatePayload, session: Session, commit: bool = True
    ) -> "Todo":
        todo = Todo(title=payload.title)
        session.add(todo)
        if commit:
            session.commit()

        return todo

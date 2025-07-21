import uuid
from datetime import datetime

from common.datetime_utils import datetime_now_with_timezone
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, SQLModel, Session, col, select

from todos.schemas import TodoCreatePayload


class TodoDataclass(BaseModel):
    id: uuid.UUID
    updated_at: datetime
    title: str
    completed: bool


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

    def to_dataclass(self) -> TodoDataclass:
        return TodoDataclass(
            id=self.id,
            updated_at=self.updated_at,
            title=self.title,
            completed=self.completed,
        )

    @staticmethod
    def create(
        payload: TodoCreatePayload, session: Session, commit: bool = True
    ) -> "TodoDataclass":
        todo = Todo(title=payload.title)
        session.add(todo)
        if commit:
            session.commit()

        return todo.to_dataclass()

    @staticmethod
    def list(session: Session) -> list[TodoDataclass]:
        query = select(Todo).order_by(col(Todo.updated_at).desc())

        return list(map(lambda todo: todo.to_dataclass(), session.exec(query).all()))

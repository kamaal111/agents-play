from pydantic import BaseModel


class TodoCreatePayload(BaseModel):
    title: str

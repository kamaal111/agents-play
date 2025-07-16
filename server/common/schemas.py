from typing import Literal

from pydantic import BaseModel


class OKResponse(BaseModel):
    detail: Literal["OK"]


class CreatedResponse(BaseModel):
    detail: Literal["Created"]


class AgentsPlayErrorDetail(BaseModel):
    type: str
    msg: str

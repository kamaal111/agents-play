from typing import Literal

from common.schemas import CreatedResponse, OKResponse
from pydantic import BaseModel, EmailStr, Field


class RegisterResponse(CreatedResponse): ...


class AccessToken(BaseModel):
    access_token: str
    expiry_timestamp: int
    token_type: Literal["bearer"]


class LoginResponse(AccessToken, OKResponse):
    refresh_token: str


class UserResponse(BaseModel):
    email: EmailStr


class SessionResponse(OKResponse):
    user: UserResponse


class RefreshResponse(AccessToken, OKResponse): ...


class RefreshPayload(BaseModel):
    refresh_token: str


class UserPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

from http import HTTPStatus
from typing import Annotated

from common.exceptions import ErrorResponse
from fastapi import APIRouter, Depends

from llm.controller import LLMControllable, get_llm_controller
from llm.schemas import (
    CreateChatMessagePayload,
    CreateChatMessageResponse,
    ListChatMessagesResponse,
)

llm_router = APIRouter(prefix="/llm")


@llm_router.get(
    "/chats/messages",
    status_code=HTTPStatus.OK,
    responses={
        HTTPStatus.OK: {
            "model": ListChatMessagesResponse,
            "description": "Returns the requesting users chat rooms",
        },
        HTTPStatus.UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Resources requested while unauthorized",
        },
        HTTPStatus.NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Chat room not found",
        },
    },
)
def list_chat_messages(
    controller: Annotated[LLMControllable, Depends(get_llm_controller)],
) -> ListChatMessagesResponse:
    return controller.list_chat_messages()


@llm_router.post(
    "/chats",
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CREATED: {
            "model": CreateChatMessageResponse,
            "description": "Return the chat response after sending a message.",
        },
        HTTPStatus.UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Resources requested while unauthorized",
        },
        HTTPStatus.FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Forbidden LLM has been selected",
        },
        HTTPStatus.INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Something unexpected went wrong",
        },
    },
)
async def create_chat_message(
    payload: CreateChatMessagePayload,
    controller: Annotated[LLMControllable, Depends(get_llm_controller)],
) -> CreateChatMessageResponse:
    return await controller.create_chat_message(payload)

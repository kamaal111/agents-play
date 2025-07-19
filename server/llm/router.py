from http import HTTPStatus
from typing import Annotated

from common.exceptions import ErrorResponse
from fastapi import APIRouter, Depends

from llm.controller import LLMControllable, get_llm_controller
from llm.schemas import ListChatMessagesResponse

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

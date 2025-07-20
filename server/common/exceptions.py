from http import HTTPStatus
from typing import Any

from common.schemas import AgentsPlayErrorDetail
from fastapi import HTTPException
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: list[AgentsPlayErrorDetail]


class AgentsPlayError(HTTPException):
    def __init__(
        self,
        status_code: HTTPStatus,
        details: list[AgentsPlayErrorDetail],
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code, list(map(_base_model_as_dict, details)), headers)


class AgentsPlayBadRequestError(AgentsPlayError):
    def __init__(self, headers: dict[str, str] | None = None):
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            [AgentsPlayErrorDetail(msg="Invalid payload", type="invalid_payload")],
            headers,
        )


class AgentsPlayNotFoundError(AgentsPlayError):
    def __init__(self, headers: dict[str, str] | None = None):
        super().__init__(
            HTTPStatus.NOT_FOUND,
            [AgentsPlayErrorDetail(msg="Not found", type="not_found")],
            headers,
        )


class AgentsPlayGeneralError(AgentsPlayError):
    def __init__(self, headers: dict[str, str] | None = None):
        super().__init__(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            [
                AgentsPlayErrorDetail(
                    msg="Something went wrong", type="internal_server_error"
                )
            ],
            headers,
        )


def _base_model_as_dict(base_model: BaseModel) -> dict[str, Any]:
    return base_model.model_dump()

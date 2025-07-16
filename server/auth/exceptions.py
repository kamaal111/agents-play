from http import HTTPStatus

from common.exceptions import AgentsPlayError
from common.schemas import AgentsPlayErrorDetail


class UserAlreadyExists(AgentsPlayError):
    def __init__(self, headers: dict[str, str] | None = None):
        super().__init__(
            HTTPStatus.CONFLICT,
            [
                AgentsPlayErrorDetail(
                    msg="User already exists", type="user_already_exists"
                )
            ],
            headers,
        )


class InvalidCredentials(AgentsPlayError):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        super().__init__(
            HTTPStatus.UNAUTHORIZED,
            [
                AgentsPlayErrorDetail(
                    msg="Invalid credentials", type="invalid_credentials"
                )
            ],
            headers,
        )

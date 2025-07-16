from typing import TYPE_CHECKING, Annotated

from database.database import get_database
from fastapi import Depends, Header

from auth.exceptions import InvalidCredentials
from auth.utils.user import get_user_by_authorization_token

if TYPE_CHECKING:
    from database.database import Databaseable

    from auth.models import User


async def get_request_user(
    authorization: Annotated[str, Header()],
    database: Annotated["Databaseable", Depends(get_database)],
) -> "User":
    user = get_user_by_authorization_token(
        authorization=authorization, database=database, verify_exp=True
    )
    if user is None:
        raise InvalidCredentials

    return user

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import jwt
from auth.conf import settings
from auth.schemas import AccessToken
from pydantic import BaseModel

if TYPE_CHECKING:
    from auth.models import User


class DecodedJWTToken(BaseModel):
    sub: str
    exp: int
    iat: int


def decode_authorization_token(
    authorization_token: str, verify_exp: bool = True
) -> DecodedJWTToken | None:
    split_authorization = authorization_token.split(" ")
    if len(split_authorization) != 2:
        return None

    if split_authorization[0].lower() != "bearer":
        return None

    try:
        claims = decode_jwt(token=split_authorization[1], verify_exp=verify_exp)
    except Exception:
        return None

    return claims


def decode_jwt(token: str, verify_exp: bool = True) -> DecodedJWTToken:
    decoded_token = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["exp", "iat", "sub"],
            "verify_exp": verify_exp,
            "verify_signature": True,
            "verify_iat": True,
            "verify_sub": True,
        },
    )

    return DecodedJWTToken(**decoded_token)


def encode_jwt(user: "User") -> AccessToken:
    now = datetime.now(settings.tzinfo)
    expire = datetime.now(settings.tzinfo) + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    access_token = jwt.encode(
        {"sub": str(user.id), "exp": expire, "iat": now},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return AccessToken(
        access_token=access_token,
        expiry_timestamp=int(expire.timestamp()),
        token_type="bearer",
    )

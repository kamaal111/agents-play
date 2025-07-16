import binascii
import os
from datetime import datetime
from typing import Optional, Sequence

import bcrypt
from common.datetime_utils import datetime_now_with_timezone
from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, SQLModel, Session, col, select

from auth.conf import settings
from auth.exceptions import UserAlreadyExists
from auth.schemas import UserPayload

HASHING_ENCODING = "utf-8"


class User(SQLModel, table=True):
    __tablename__: str = "user"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    password: str = Field(min_length=8)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=datetime_now_with_timezone,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            onupdate=datetime_now_with_timezone,
        ),
        default_factory=datetime_now_with_timezone,
    )

    @classmethod
    def create(
        cls, payload: UserPayload, session: Session, commit: bool = True
    ) -> "User":
        existing_user = cls.get_by_email(email=payload.email, session=session)
        if existing_user is not None:
            raise UserAlreadyExists()

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(
            payload.password.encode(HASHING_ENCODING), salt
        ).decode(HASHING_ENCODING)
        user = User(email=payload.email, password=hashed_password)

        session.add(user)
        if commit:
            session.commit()

        return user

    @staticmethod
    def get_by_email(email: str, session: Session) -> Optional["User"]:
        query = select(User).where(User.email == email).limit(1)

        return session.exec(query).first()

    @staticmethod
    def get_by_id(id: int, session: Session) -> Optional["User"]:
        query = select(User).where(User.id == id).limit(1)

        return session.exec(query).first()

    def verify_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode(HASHING_ENCODING),
            self.password.encode(HASHING_ENCODING),
        )


class UserToken(SQLModel, table=True):
    __tablename__: str = "user_token"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field()
    user_id: int = Field(default=None, foreign_key=f"{User.__tablename__}.id")
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=datetime_now_with_timezone
        ),
    )

    def verify_key(self, raw_key: str) -> bool:
        return bcrypt.checkpw(
            raw_key.encode(HASHING_ENCODING),
            self.key.encode(HASHING_ENCODING),
        )

    @classmethod
    def create(cls, user: User, session: Session) -> str:
        tokens_for_user = cls.get_all_for_user(user=user, session=session)
        tokens_to_delete_amount = len(tokens_for_user) - (
            settings.refresh_tokens_per_user - 1
        )

        assert len(tokens_for_user) <= settings.refresh_tokens_per_user, (
            "Tokens should have been less then the amount allowed"
        )

        if tokens_to_delete_amount > 0:
            tokens_to_delete = tokens_for_user[:tokens_to_delete_amount]
            for token_to_delete in tokens_to_delete:
                session.delete(token_to_delete)

        refresh_token = cls.__generate_refresh_token()
        salt = bcrypt.gensalt()
        hashed_refresh_token = bcrypt.hashpw(
            refresh_token.encode(HASHING_ENCODING), salt
        ).decode(HASHING_ENCODING)

        token = UserToken(key=hashed_refresh_token, user_id=user.id)
        session.add(token)

        session.commit()

        return refresh_token

    @staticmethod
    def get_all_for_user(user: User, session: Session) -> Sequence["UserToken"]:
        query = (
            select(UserToken)
            .where(UserToken.user_id == user.id)
            .order_by(col(UserToken.created_at).asc())
        )

        return session.exec(query).all()

    @staticmethod
    def __generate_refresh_token() -> str:
        return binascii.hexlify(os.urandom(20)).decode()

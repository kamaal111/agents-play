from common.conf import BaseSettings


class __Settings(BaseSettings):
    jwt_expire_minutes: int = 30
    jwt_secret_key: str = "not_so_secure_secret"
    jwt_algorithm: str = "HS256"
    refresh_tokens_per_user: int = 4


settings = __Settings()  # type: ignore

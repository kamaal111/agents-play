from common.conf import BaseSettings

DATABASE_USER = "agents-play-user"
DATABASE_PASSWORD = "secure-password"
DATABASE_HOST = "db"
DATABASE_PORT = "5432"
DATABASE_NAME = "agents_play_db"
DEFAULT_POSTGRES_DSN = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"


class __Settings(BaseSettings):
    database_url: str = DEFAULT_POSTGRES_DSN


settings = __Settings()  # type: ignore

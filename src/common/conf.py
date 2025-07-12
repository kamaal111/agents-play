from pydantic import HttpUrl
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: str
    forex_base_api_url: HttpUrl

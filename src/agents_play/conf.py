from pydantic_settings import BaseSettings, SettingsConfigDict


class __Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: str


settings = __Settings()

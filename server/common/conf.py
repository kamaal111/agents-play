import pytz
from pydantic_extra_types.timezone_name import TimeZoneName
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    openai_api_key: str
    timezone: TimeZoneName = TimeZoneName("UTC")

    @property
    def tzinfo(self) -> pytz.BaseTzInfo:
        timezone = pytz.timezone(self.timezone)

        return timezone


settings = BaseSettings()  # type: ignore

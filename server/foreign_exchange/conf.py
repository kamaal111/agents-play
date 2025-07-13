from common.conf import BaseSettings
from pydantic import HttpUrl


class __Settings(BaseSettings):
    forex_base_api_url: HttpUrl


settings = __Settings()  # type: ignore

from pydantic import HttpUrl

from common.conf import BaseSettings


class __Settings(BaseSettings):
    forex_base_api_url: HttpUrl


settings = __Settings()  # type: ignore

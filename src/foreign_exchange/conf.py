from common.conf import BaseSettings


class __Settings(BaseSettings): ...


settings = __Settings()  # type: ignore

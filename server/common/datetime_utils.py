from datetime import datetime

from common.conf import settings


def datetime_now_with_timezone() -> datetime:
    return datetime.now(tz=settings.tzinfo)

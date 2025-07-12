import os
import urllib

import aiohttp

from foreign_exchange.conf import settings
from foreign_exchange.responses import Currencies, RatesResponse


class ForeignExchangeClient:
    async def get_rates(self, base: Currencies) -> RatesResponse:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.__url}?{urllib.parse.urlencode({'base': base})}"
            ) as response:
                response.raise_for_status()
                json_data = await response.json()

                return RatesResponse(**json_data)

    @property
    def __url(self) -> str:
        return os.path.join(str(settings.forex_base_api_url), "v1/rates/latest")

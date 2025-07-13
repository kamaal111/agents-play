from pydantic import BaseModel

from foreign_exchange.currencies import Currencies


class RatesResponse(BaseModel):
    base: Currencies
    date: str
    rates: dict[Currencies, float]

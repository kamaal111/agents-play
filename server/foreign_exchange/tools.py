from typing import cast

from langchain_core.tools import tool

from foreign_exchange.client import ForeignExchangeClient
from foreign_exchange.currencies import CURRENCIES, Currencies

foreign_exchange_client = ForeignExchangeClient()


@tool
async def get_exchange_rates_tool(base_currency: str) -> dict[Currencies, float]:
    """Get current foreign exchange rates for a base currency.

    Args:
        base_currency: The 3-letter currency code to use as base (e.g., 'USD', 'EUR', 'GBP')

    Returns:
        Dictionary mapping currency codes to their exchange rates relative to the base currency
    """

    base_currency_upper = base_currency.strip().upper()
    if base_currency_upper not in CURRENCIES:
        raise ValueError(
            f"Unsupported currency: {base_currency}. Must be one of: {', '.join(CURRENCIES)}"
        )

    # Cast to proper type since we validated above
    validated_base_currency = cast(Currencies, base_currency_upper)

    try:
        response = await foreign_exchange_client.get_rates(base=validated_base_currency)
    except Exception as e:
        raise RuntimeError(
            f"Failed to get exchange rates for '{base_currency}': {str(e)}"
        )

    return response.rates

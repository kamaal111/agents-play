from foreign_exchange.currencies import Currencies
from foreign_exchange.graph import foreign_exchange_rate_invoke
from langchain_core.tools import tool


@tool
async def get_exchange_rates_tool(user_request: str) -> dict[Currencies, float] | str:
    """
    Get current foreign exchange rates for various currencies based on user request.

    This tool retrieves real-time or recent foreign exchange rates for different
    currency pairs. It can handle various types of currency-related requests such as
    converting between specific currencies, getting rates for multiple currencies,
    or providing exchange rate information for trading or travel purposes.

    Args:
        user_request (str): Natural language request describing what exchange rates
            the user wants. Examples:
            - "What's the USD to EUR exchange rate?"
            - "Convert 100 dollars to yen"
            - "Show me rates for GBP, EUR, and JPY"
            - "What's the current exchange rate from British pounds to US dollars?"

    Returns:
        dict[Currencies, float] | str: Either a dictionary mapping currency codes
            to their exchange rates as floating point numbers, or an error message
            string if the request could not be processed.

            Success example: {Currencies.USD: 1.0, Currencies.EUR: 0.85}
            Error example: "Unable to fetch exchange rates for the requested currencies"

    Note:
        The function handles various currency formats and can interpret natural
        language requests to determine which currencies the user is interested in.
        If there's an error fetching the rates, a descriptive error message is returned.
    """

    result = await foreign_exchange_rate_invoke(request=user_request)
    if result.failure_message is not None:
        return result.failure_message

    return result.rates

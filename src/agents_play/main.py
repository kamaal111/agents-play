from typing import cast

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from agents_play.conf import settings
from foreign_exchange.currencies import (
    CURRENCIES,
    CURRENCIES_MAPPED_TO_NAMES,
    Currencies,
)

assert settings.openai_api_key

gpt4o_mini_model = init_chat_model("gpt-4o-mini", model_provider="openai")

human_forex_decision = input("Which currency do you want to know the rates of today?\n")
human_message = HumanMessage(content=human_forex_decision, name="Kamaal")

identify_currency_code_prompt = f"""
You are a currency identification assistant. Based on the user's input, determine which currency they are referring to.

Available currencies and their symbols:
{"\n".join([f"- {symbol}: {name}" for symbol, name in CURRENCIES_MAPPED_TO_NAMES.items()])}

User input: "{human_forex_decision}"

Please respond with ONLY the 3-letter currency symbol (e.g., "USD", "EUR", "GBP") that best matches the user's input.
If the user mentions a currency name, country, or partial match, return the corresponding symbol.
If you cannot determine a clear match, respond with "UNKNOWN".

Currency symbol:
""".strip()

gpt4o_mini_model_message = gpt4o_mini_model.invoke(identify_currency_code_prompt)
assert isinstance(gpt4o_mini_model_message.content, str)

identified_currency_code = gpt4o_mini_model_message.content.strip().upper()

if identified_currency_code not in CURRENCIES:
    raise Exception(f"'{human_forex_decision}' is an unknown forex")

# Validated above so its safe to cast
identified_currency_code = cast(Currencies, identified_currency_code)

print(CURRENCIES_MAPPED_TO_NAMES[identified_currency_code])

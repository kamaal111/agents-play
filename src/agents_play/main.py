from langchain.chat_models import init_chat_model

from agents_play.conf import settings

assert settings.openai_api_key, (
    'Must have "OPENAI_API_KEY" in the environment for this app to function'
)

model = init_chat_model("gpt-4o-mini", model_provider="openai")
message = model.invoke("Hello, world!")
print(message.content)

from app_api.router import app_api_router
from fastapi import FastAPI
from health.router import health_router

from agents_play.conf import settings

assert settings.openai_api_key

app = FastAPI()

app.include_router(health_router)
app.include_router(app_api_router)

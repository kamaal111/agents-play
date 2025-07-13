from fastapi import FastAPI
from health.router import health_router

app = FastAPI()

app.include_router(health_router)

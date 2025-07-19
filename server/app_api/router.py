from fastapi import APIRouter
from llm.router import llm_router

app_api_router = APIRouter(prefix="/app-api/v1")

app_api_router.include_router(llm_router)

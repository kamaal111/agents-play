from auth.router import auth_router
from fastapi import APIRouter

app_api_router = APIRouter(prefix="/app-api/v1")

app_api_router.include_router(auth_router)

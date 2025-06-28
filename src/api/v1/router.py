from fastapi import APIRouter

from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.client import router as client_router

api_router = APIRouter()

api_router.include_router(client_router)
api_router.include_router(auth_router)

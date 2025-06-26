import logging
from typing import Optional

from fastapi import APIRouter

from api.v1.schema.auth import AuthResponse
from services.authorize_service import auth_client, auth_client_callback

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/auth", response_model=AuthResponse)
def auth():
    return auth_client()


@router.get("/auth/callback")
async def auth_callback(
    state: Optional[str] = None,
    code: Optional[str] = None,
):
    return auth_client_callback(state, code)

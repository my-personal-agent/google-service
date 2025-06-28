import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import RedirectResponse

from api.v1.schema.auth import AuthResponse
from enums.auth_type import AuthType
from services.auth_service import auth_client, auth_client_callback

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/auth", response_model=AuthResponse)
async def auth(
    client_id: Annotated[UUID, Query(...)],
    auth_type: Annotated[AuthType, Query(...)],
    current_uri: Optional[str] = Query(
        default=None, description="(Optional) the original URI to return to after OAuth"
    ),
):
    return await auth_client(str(client_id), auth_type, str(current_uri))


@router.get(
    "/auth/callback", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND
)
async def auth_callback(
    state: Optional[str] = None,
    code: Optional[str] = None,
):
    return await auth_client_callback(state, code)

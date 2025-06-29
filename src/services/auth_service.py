import logging
from urllib.parse import quote_plus, urlencode

import googleapiclient.discovery
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from api.v1.schema.auth import AuthResponse
from config.settings_config import get_settings
from core.utils import get_google_client_config
from db.prisma.generated.enums import AuthType as PrismaAuthTye
from db.prisma.utils import get_db
from enums.auth_type import AuthType

logger = logging.getLogger(__name__)


async def auth_client(
    client_id: str, auth_type: AuthType, current_uri: str
) -> AuthResponse:
    db = await get_db()

    client_auth = await db.clientauth.find_first(
        where={"clientId": client_id, "authType": PrismaAuthTye(auth_type.value)}
    )

    if not client_auth:
        raise HTTPException(400, "Client not found")

    flow = Flow.from_client_config(
        get_google_client_config(client_auth),
        scopes=client_auth.scopes,
        redirect_uri=str(get_settings().google_redirect_uri),
    )
    url, state = flow.authorization_url(access_type="offline", prompt="consent")

    db = await get_db()
    await db.oauthflow.create(
        {"state": state, "clientAuthId": client_auth.id, "currentUri": current_uri}
    )

    return AuthResponse(url=url)


async def auth_client_callback(state: str | None, code: str | None) -> RedirectResponse:
    if not state or not code:
        raise HTTPException(400, "Missing code or state")

    db = await get_db()
    existing = await db.oauthflow.find_unique(
        where={"state": state}, include={"clientAuth": True}
    )
    if not existing or not existing.clientAuth:
        raise HTTPException(400, "Invalid state")

    await db.oauthflow.delete(where={"state": state})

    flow = Flow.from_client_config(
        get_google_client_config(existing.clientAuth),
        scopes=existing.clientAuth.scopes,
        redirect_uri=get_settings().google_redirect_uri,
        state=state,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    if not creds.token or not creds.expiry:
        raise HTTPException(500, "Token missing")

    # Get user info
    oauth2 = googleapiclient.discovery.build("oauth2", "v2", credentials=creds)
    profile = oauth2.userinfo().get().execute()
    google_id = profile["id"]

    user_token = await db.usertoken.upsert(
        where={
            "googleId_clientAuthId": {
                "googleId": google_id,
                "clientAuthId": existing.clientAuthId,
            }
        },
        data={
            "create": {
                "googleId": google_id,
                "accessToken": creds.token,
                "refreshToken": creds.refresh_token or "",
                "expiry": creds.expiry,
                "clientAuthId": existing.clientAuthId,
            },
            "update": {
                "accessToken": creds.token,
                "refreshToken": creds.refresh_token or "",
                "expiry": creds.expiry,
            },
        },
    )

    # Ensure current_uri is a string, or empty if None
    current = existing.currentUri or ""

    # Use urlencode to safely build the query params
    params = {
        "google_id": user_token.id,
        "auth_type": existing.clientAuth.authType,
        "current_uri": current,
    }
    query = urlencode(params, quote_via=quote_plus)

    redirect_to = f"{existing.clientAuth.redirectUri}?{query}"
    return RedirectResponse(redirect_to, status_code=status.HTTP_302_FOUND)


async def get_creds(user_token_id: str) -> Credentials:
    db = await get_db()
    user_token = await db.usertoken.find_unique(
        where={"id": user_token_id}, include={"clientAuth": True}
    )
    if not user_token or not user_token.clientAuth:
        raise HTTPException(404, "User token not found")

    creds = Credentials(
        token=user_token.accessToken,
        refresh_token=user_token.refreshToken or None,
        token_uri=str(get_settings().google_token_uri),
        client_id=user_token.clientAuth.googleClientId,
        client_secret=user_token.clientAuth.googleClientSecret,
        scopes=user_token.clientAuth.scopes,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(GRequest())

        if not creds.token or not creds.expiry:
            raise HTTPException(
                status_code=500, detail="Credentials missing token or expiry"
            )

        await db.usertoken.update(
            where={"id": user_token.id},
            data={"accessToken": creds.token, "expiry": creds.expiry},
        )

    return creds

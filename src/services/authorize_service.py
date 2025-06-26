from typing import Optional

from fastapi import HTTPException
from google.auth.transport.requests import Request as GRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from api.v1.schema.auth import AuthCallbackResponse, AuthResponse
from config.settings_config import get_settings
from db.prisma.utils import get_db


async def auth_client() -> AuthResponse:
    flow = Flow.from_client_config(
        get_settings().google_client_config,
        scopes=get_settings().google_scopes,
        redirect_uri=get_settings().google_redirect_uri,
    )
    url, state = flow.authorization_url(access_type="offline", prompt="consent")
    return AuthResponse(url=url, state=state)


async def auth_client_callback(
    state: Optional[str], code: Optional[str]
) -> AuthCallbackResponse:
    flow = Flow.from_client_config(
        get_settings().google_client_config,
        scopes=get_settings().google_scopes,
        state=state,
        redirect_uri=get_settings().google_redirect_uri,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    user_id = profile["emailAddress"]

    if not creds.token or not creds.expiry:
        raise HTTPException(
            status_code=500, detail="Credentials missing token or expiry"
        )

    db = await get_db()

    await db.tokeninfo.upsert(
        where={"userId": user_id},
        data={
            "create": {
                "userId": user_id,
                "accessToken": creds.token,
                "refreshToken": creds.refresh_token,
                "expiry": creds.expiry,
            },
            "update": {
                "accessToken": creds.token,
                "refreshToken": creds.refresh_token,
                "expiry": creds.expiry,
            },
        },
    )

    return AuthCallbackResponse(status="OK", user_id=user_id)


async def get_creds(user_id: str) -> Credentials:
    db = await get_db()

    token_info = await db.tokeninfo.find_unique(where={"userId": user_id})
    if not token_info:
        raise HTTPException(404, "User not found")

    creds = Credentials(
        token=token_info.accessToken,
        refresh_token=token_info.refreshToken,
        token_uri=get_settings().google_token_uri,
        client_id=get_settings().google_client_id,
        client_secret=get_settings().google_client_secret,
        expiry=token_info.expiry,
    )
    if creds.expired:
        creds.refresh(GRequest())

        if not creds.token or not creds.expiry:
            raise HTTPException(
                status_code=500, detail="Credentials missing token or expiry"
            )

        await db.tokeninfo.update(
            where={"userId": user_id},
            data={
                "accessToken": creds.token,
                "expiry": creds.expiry,
                "refreshToken": (
                    creds.refresh_token
                    if creds.refresh_token
                    else token_info.refreshToken
                ),
            },
        )
    return creds

import logging

from fastapi import HTTPException

from api.v1.schema.client import AddClientAuthsRequest, ClientRequest, ClientResponse
from db.prisma.generated.enums import AuthType as PrismaAuthType
from db.prisma.utils import get_db

logger = logging.getLogger(__name__)


async def create_client(payload: ClientRequest) -> ClientResponse:
    db = await get_db()

    client = await db.client.create(
        data={
            "name": payload.name,
        }
    )

    return ClientResponse(id=client.id, name=client.name)


async def add_client_auths(
    payload: AddClientAuthsRequest,
) -> None:
    db = await get_db()

    client = await db.client.find_unique(where={"id": str(payload.client_id)})
    if not client:
        raise HTTPException(400, "Client not found")

    await db.clientauth.create_many(
        [
            {
                "authType": PrismaAuthType(auth.auth_type.value),
                "googleClientId": auth.google_client_id,
                "googleClientSecret": auth.google_client_secret,
                "redirectUri": str(auth.redirect_uri),
                "scopes": auth.scopes,
                "clientId": str(client.id),
            }
            for auth in payload.auths
        ]
    )

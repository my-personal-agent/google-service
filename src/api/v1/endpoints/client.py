import logging

from fastapi import APIRouter, status

from api.v1.schema.client import AddClientAuthsRequest, ClientRequest, ClientResponse
from services.client_service import add_client_auths, create_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/client", status_code=status.HTTP_201_CREATED, response_model=ClientResponse
)
async def create(payload: ClientRequest):
    return await create_client(payload)


@router.post("/client/auths", status_code=status.HTTP_201_CREATED)
async def add_auths(payload: AddClientAuthsRequest):
    return await add_client_auths(payload)

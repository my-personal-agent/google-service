from typing import List
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

from enums.auth_type import AuthType


class ClientRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Client name")


class ClientResponse(BaseModel):
    id: str
    name: str


class ClientAuthRequest(BaseModel):
    auth_type: AuthType
    google_client_id: str = Field(..., min_length=20, description="Google Client ID")
    google_client_secret: str = Field(
        ..., min_length=20, description="Google Client Secret"
    )
    redirect_uri: AnyHttpUrl = Field(
        ..., description="Authorized redirect URI (http(s) URL)"
    )
    scopes: List[str] = Field(
        ..., min_length=1, description="OAuth scopes — at least one required"
    )


class AddClientAuthsRequest(BaseModel):
    client_id: UUID = Field(..., description="Client ID")
    auths: List[ClientAuthRequest] = Field(
        ..., min_length=1, description="Types - at least one required"
    )

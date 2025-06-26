import logging
from functools import lru_cache
from typing import Annotated, List

from pydantic import AnyHttpUrl, BeforeValidator, Field, ValidationError, computed_field
from pydantic_settings import BaseSettings

from enums.mcp_transport import McpTransport

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    env: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]

    # API
    project_name: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    project_version: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    backend_cors_origins: List[AnyHttpUrl]
    allowed_hosts: List[AnyHttpUrl]

    # mcp
    mcp_host: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    mcp_port: Annotated[int, Field(ge=0)]
    mcp_transport: McpTransport

    # google
    google_client_id: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    google_client_secret: Annotated[
        str, BeforeValidator(str.strip), Field(min_length=1)
    ]
    google_redirect_uri: AnyHttpUrl
    google_auth_uri: AnyHttpUrl
    google_token_uri: AnyHttpUrl
    google_scopes: List[AnyHttpUrl]

    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"
        use_enum_values = True

    @computed_field
    def project_info(self) -> str:
        return f"{self.project_name} - {self.project_version}"

    @computed_field
    def google_client_config(self) -> dict:
        return {
            "web": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "auth_uri": self.google_auth_uri,
                "token_uri": self.google_token_uri,
            }
        }


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore
    except ValidationError as e:
        logger.error("Environment configuration error:")
        logger.error(e)
        raise RuntimeError("Shutting down due to bad config")

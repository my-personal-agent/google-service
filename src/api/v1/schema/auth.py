from pydantic import AnyHttpUrl, BaseModel


class AuthResponse(BaseModel):
    url: AnyHttpUrl

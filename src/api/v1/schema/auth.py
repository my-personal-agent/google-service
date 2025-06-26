from pydantic import AnyHttpUrl, BaseModel


class AuthResponse(BaseModel):
    url: AnyHttpUrl
    state: str


class AuthCallbackResponse(BaseModel):
    status: str
    user_id: str

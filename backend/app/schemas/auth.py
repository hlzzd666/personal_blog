from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class AdminSessionResponse(BaseModel):
    username: str
    logged_in_at: str
    expires_at: str

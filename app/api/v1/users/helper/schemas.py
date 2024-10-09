from typing import Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    verified: Optional[bool] = (
        False  # Model won't have this key because user not input status
    )


class AccessTokenResponse(BaseModel):
    access_token: str

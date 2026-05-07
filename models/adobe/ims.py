from pydantic import BaseModel, Field
import time


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    created_at: float
    claims: dict

    @property
    def is_expired(self) -> bool:
        expires_at = self.created_at + self.expires_in
        return (expires_at - time.time()) < 3600
from pydantic import BaseModel, Field
import time

class TokenResponse(BaseModel):
    expires_in: int
    access_token: str
    fetched_at: float = Field(default_factory=time.time)

    @property
    def is_expired(self)->bool:
        expires_at = self.fetched_at + self.expires_in
        return (expires_at - time.time()) < 3600
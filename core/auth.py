import logging

from authlib.integrations.requests_client import OAuth2Session
from config.environment import get_env, write_env
from models.adobe.ims import TokenResponse
from config.endpoints import BaseUrls
import certifi
import json, base64

logger = logging.getLogger(__name__)


class Auth:
    """Manages OAuth2 client-credentials authentication with Adobe IMS."""

    def __init__(self):
        self.env = get_env()
        self._token: TokenResponse | None = None
        self._bootstrap()

    @property
    def token(self) -> TokenResponse:
        """Current access token; auto-refreshes when expired."""
        if self._token is None or self._token.is_expired:
            self._token = self.ensure_token()
        return self._token

    def refresh(self) -> TokenResponse:
        """Force-fetch a new token regardless of expiry."""
        self._token = self.ensure_token()
        return self._token

    def ensure_token(self) -> TokenResponse:
        """Return a valid token, fetching one only if the cached token is missing or expired."""
        if self._token is None or self._token.is_expired:
            self._token = self._fetch_token()
        return self._token

    def _fetch_token(self) -> TokenResponse:
        """Exchange client credentials for a new access token from Adobe IMS."""
        logger.debug("Fetching access token from Adobe IMS")
        session = OAuth2Session(
            client_id=self.env.client_id,
            client_secret=self.env.client_secret,
            scope=self.env.scopes,
        )
        session.verify = certifi.where()

        raw = session.fetch_token(
            url=BaseUrls.TOKEN_URL,
            grant_type="client_credentials",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        decoded = self._decode_token(raw["access_token"])
        raw["created_at"] = int(decoded["created_at"]) / 1000
        raw["claims"] = decoded

        token = TokenResponse(**raw)
        return token

    def _bootstrap(self) -> None:
        """Persist ORG_ID and TECHNICAL_ACCOUNT_ID to .env on first run if not already set."""
        if self.env.org_id and self.env.technical_account_id:
            return
        self._token = self.ensure_token()

        org_id = self._token.claims.get("org")
        tech_id = self._token.claims.get("client_id")

        logger.info("Bootstrap: writing ORG_ID and TECHNICAL_ACCOUNT_ID to .env")
        self.env = write_env({"ORG_ID": org_id, "TECHNICAL_ACCOUNT_ID": tech_id})

    @staticmethod
    def _decode_token(token: str) -> dict:
        """Decode the JWT payload section without verifying the signature."""
        parts = token.split(".")
        payload = parts[1]
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))
        return data

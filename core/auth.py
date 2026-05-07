from authlib.integrations.requests_client import OAuth2Session
from config.environment import Env
from models.adobe.ims import TokenResponse
from config.environment import write_env
from config.endpoints import BaseUrls
import certifi
import json, base64


class Auth:
    def __init__(self):
        self.env = Env()
        self._token: TokenResponse | None = None
        self._bootstrap()

    @property
    def token(self) -> TokenResponse:
        if self._token is None or self._token.is_expired:
            self._token = self.ensure_token()
        return self._token

    def refresh(self) -> TokenResponse:
        """Force-refresh the token"""
        self._token = self.ensure_token()
        return self._token
    
    def ensure_token(self):
        if self._token is None or self._token.is_expired:
            self._token = self._fetch_token()
        return self._token

    def _fetch_token(self) -> TokenResponse:
        session = OAuth2Session(
            client_id=self.env.client_id,
            client_secret=self.env.client_secret,
            scope=self.env.scopes,
        )
        session.verify = False #certifi.where() TODO Change

        raw = session.fetch_token(
            url=f"{BaseUrls.IMS_ENDPOINT}/ims/token/v3",
            grant_type="client_credentials",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        decoded = self._decode_token(raw["access_token"])
        raw["created_at"] = int(decoded["created_at"]) / 1000
        raw["claims"] = decoded

        token = TokenResponse(**raw)
        return token

    def _bootstrap(self) -> None:
        if self.env.org_id and self.env.technical_account_id:
            return
        self._token = self.ensure_token()

        org_id = self._token.claims.get("org")
        tech_id = self._token.claims.get("client_id")

        write_env({"ORG_ID": org_id, "TECHNICAL_ACCOUNT_ID": tech_id})

        self.env.org_id = org_id
        self.env.technical_account_id = tech_id

        self.env = Env()

    @staticmethod
    def _decode_token(token: str) -> dict:
        parts = token.split(".")
        payload = parts[1]
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))
        return data

from authlib.integrations.requests_client import OAuth2Session
from config.environment import Env
from models.adobe.ims import TokenResponse


class Auth:

    def __init__(self):
        self.env = Env()
        self._token: TokenResponse | None = None

    @property
    def token(self) -> TokenResponse:
        self.ensure_token()
        return self._token

    def ensure_token(self, force: bool = False):
        if force or self._token is None or self._token.is_expired:
            self._token = self._fetch_token()

    def _fetch_token(self) -> TokenResponse:
        token_endpoint = f'{self.env.ims_endpoint}/ims/token/v3'
        session = OAuth2Session(
            client_id=self.env.client_id,
            client_secret=self.env.client_secret,
            scope=self.env.scopes,
            org_id=None
        )

        token = session.fetch_token(
            url=token_endpoint,
            grant_type='client_credentials',
            scope=self.env.scopes,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        return TokenResponse(**token)

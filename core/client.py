import requests
from core.auth import Auth
from config.environment import Env, write_env


class AdobeClient:

    def __init__(self):
        self.auth = Auth()

        if not self.auth.env.technical_account_id or not self.auth.env.global_company_id or not self.auth.env.org_id:
            me = self.discover_me()
            org = me.ims_orgs[0]
            company = org.companies[0]
            write_env({
                'TECHNICAL_ACCOUNT_ID': me.ims_user_id,
                'GLOBAL_COMPANY_ID': company.global_company_id,
                'ORG_ID': org.img_org_id,
            })
            self.auth.env = Env()

    def _authenticated_request(self, method: str, url: str, **kwargs):
        self.auth.ensure_token()
        headers = {
            **kwargs.pop('headers', {}),
            'Authorization': f'Bearer {self.auth.token.access_token}',
            'accept': 'application/json',
            'x-api-key': self.auth.env.client_id,
        }

        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            self.auth.ensure_token(force=True)
            headers['Authorization'] = f'Bearer {self.auth.token.access_token}'
            response = requests.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()
        return response

    # TODO: implement when hitting reporting APIs at volume
    # Retry on 429 (rate limit) and 5xx (transient). Exponential backoff.
    # Called by _authenticated_request, wrapping the actual requests.request call.
    def _request_with_retry(self, method: str, url: str, headers: dict, **kwargs) -> requests.Response:
        requests.Session()
        raise NotImplementedError

    def discover_me(self):
        from models.adobe.analytics import DiscoveryResponse
        url = f"{self.auth.env.aa_endpoint}/discovery/me"
        response = self._authenticated_request('get', url)
        return DiscoveryResponse(**response.json())

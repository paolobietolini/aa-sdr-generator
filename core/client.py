import requests
from core.auth import Auth
from config.environment import Env, write_env
import certifi
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from models.adobe.analytics import DiscoveryResponse, SuiteResponse, MetricResponse
from typing import Optional
from config.endpoints import BaseUrls, AAEndpoints
from pydantic import TypeAdapter


class AdobeClient:
    def __init__(self):
        self.auth = Auth()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            respect_retry_after_header=True,
        )

        session.mount("https://", HTTPAdapter(max_retries=retries))

        session.headers.update(
            {
                "accept": "application/json",
                "x-api-key": self.auth.env.client_id,
            }
        )

        session.verify = False  # certifi.where() TODO Change

        return session

    def _update_auth_header(self) -> None:
        """Sync the session's Authorization header with the current token."""
        self.session.headers["Authorization"] = f"Bearer {self.auth.token.access_token}"

    def _authenticated_request(
        self, method: str, url: str, **kwargs
    ) -> requests.Request:
        self.auth.ensure_token()
        self._update_auth_header()

        response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            self.auth.refresh()
            self._update_auth_header()
            response = self.session.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    def _paginated_request(self, method: str, url: str, **kwargs) -> requests.Request:
        self.auth.ensure_token()
        self._update_auth_header()

        elements = []
        page = 0

        while True:
            params = kwargs.get("params", {})
            params.update({"page": page, "limit": 100})

            kwargs["params"] = params

            response = self._authenticated_request(method, url, **kwargs)
            data = response.json()
            print(data)
            elements.extend(data.get("content", []))

            if data.get("lastPage", True):
                break

            page += 1

        return elements

    def discover_me(self) -> DiscoveryResponse:

        url = f"{BaseUrls.AA_ENDPOINT}{AAEndpoints.DISCOVERY}"
        response = self._authenticated_request("get", url)
        return DiscoveryResponse(**response.json())


class AdobeAnalyticsClient:
    def __init__(self, client: AdobeClient):
        self.client = client
        self.env = self.client.auth.env
        self.api_endpoint = (
            f"{BaseUrls.AA_ENDPOINT}/api/{self._get_global_company_id()}"
        )

    def _get_global_company_id(self):
        if self.env.global_company_id is None:
            me = self.client.discover_me()
            orgs = me.ims_orgs[0]
            company = orgs.companies[0]
            global_company_id = company.global_company_id
            write_env({"GLOBAL_COMPANY_ID": global_company_id})
            self.client.auth.env = Env()
        return self.env.global_company_id

    def get_suite(self, rsid: str, **kwargs) -> SuiteResponse:
        url = f"{self.api_endpoint}{AAEndpoints.SUITES}/{rsid}"
        data = self.client._authenticated_request("get", url, **kwargs).json()
        return SuiteResponse.model_validate(data)

    def get_suites(self, **kwargs) -> list[SuiteResponse]:
        url = f"{self.api_endpoint}{AAEndpoints.SUITES}"
        data = self.client._paginated_request("get", url, **kwargs)
        return TypeAdapter(list[SuiteResponse]).validate_python(data)

    def get_metric(self,id: str,rsid: str,locale: Optional[str] = None,
        expansion: Optional[str] = None,**kwargs,) -> MetricResponse:
        url = f"{self.api_endpoint}{AAEndpoints.METRICS}/{id}"

        params = kwargs.pop("params", {}) or {}
        params["rsid"] = rsid
        if locale is not None:
            params["locale"] = locale
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params
        metric = self.client._authenticated_request("get", url, **kwargs).json()
        return MetricResponse(**metric)
    
    
    def get_metrics(self,rsid: str,locale: Optional[str] = None,segmentable: Optional[bool] = None,expansion: Optional[str] = None,**kwargs) -> list[MetricResponse]:
        url = f"{self.api_endpoint}{AAEndpoints.METRICS}"

        params = kwargs.pop("params", {}) or {}
        params["rsid"] = rsid

        if locale is not None:
            params["locale"] = locale
        if segmentable is not None:
            params["segmentable"] = str(segmentable).lower() 
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params

        data = self.client._authenticated_request("get", url, **kwargs).json()

        return TypeAdapter(list[MetricResponse]).validate_python(data)

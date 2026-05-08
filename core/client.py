import logging
import requests
from urllib.parse import quote
from core.auth import Auth
from config.environment import write_env
import certifi
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from models.adobe.analytics import (
    DiscoveryResponse,
    SuiteResponse,
    MetricResponse,
    DimensionResponse,
    CalculatedMetricResponse,
    SegmentResponse,
)
from typing import Optional
from config.endpoints import AAEndpoints
from pydantic import TypeAdapter

logger = logging.getLogger(__name__)


class AdobeClient:
    """Raw HTTP client for Adobe APIs with authentication, retry logic, and pagination."""

    def __init__(self):
        self.auth = Auth()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Build a requests Session with retry logic and default headers."""
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

        session.verify = certifi.where()

        return session

    def _update_auth_header(self) -> None:
        """Sync the session's Authorization header with the current token."""
        self.session.headers["Authorization"] = f"Bearer {self.auth.token.access_token}"

    def _authenticated_request(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """Make an authenticated request, retrying once after a 401 with a fresh token."""
        self.auth.ensure_token()
        self._update_auth_header()

        response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            logger.warning("401 on %s %s — refreshing token and retrying", method.upper(), url)
            self.auth.refresh()
            self._update_auth_header()
            response = self.session.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    def _paginated_request(self, method: str, url: str, **kwargs) -> list:
        """Collect all pages from a paginated endpoint and return a flat list of items."""
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

            elements.extend(data.get("content", []))
            logger.debug("Page %d fetched — %d items total", page, len(elements))

            if data.get("lastPage", True):
                break

            page += 1

        return elements

    def discover_me(self) -> DiscoveryResponse:
        """Call /discovery/me and return the parsed IMS organisations response."""
        url = AAEndpoints.discovery_url()
        response = self._authenticated_request("get", url)
        return DiscoveryResponse(**response.json())


class AdobeAnalyticsClient:
    """Adobe Analytics API client built on top of AdobeClient."""

    def __init__(self, client: AdobeClient):
        self.client = client
        self.env = self.client.auth.env
        self._company_name: str | None = None
        self.api_endpoint = AAEndpoints.api_base(self._get_global_company_id())

    def _get_global_company_id(self) -> str:
        """Resolve the global company ID, persisting it to .env if not already set."""
        if self.env.global_company_id is None:
            me = self.client.discover_me()
            orgs = me.ims_orgs[0]
            company = orgs.companies[0]
            self._company_name = company.company_name
            global_company_id = company.global_company_id
            self.env = write_env({"GLOBAL_COMPANY_ID": global_company_id})
        return self.env.global_company_id

    @property
    def company_name(self) -> str:
        """Cached company name from /discovery/me; fetches once on first access."""
        if self._company_name is None:
            me = self.client.discover_me()
            self._company_name = me.ims_orgs[0].companies[0].company_name
        return self._company_name

    def get_suite(self, rsid: str, **kwargs) -> SuiteResponse:
        """Fetch a single report suite by rsid."""
        url = f"{self.api_endpoint}{AAEndpoints.SUITES}/{quote(rsid, safe='')}"
        data = self.client._authenticated_request("get", url, **kwargs).json()
        return SuiteResponse.model_validate(data)

    def get_suites(self, **kwargs) -> list[SuiteResponse]:
        """Fetch all report suites accessible to the authenticated user."""
        url = f"{self.api_endpoint}{AAEndpoints.SUITES}"
        data = self.client._paginated_request("get", url, **kwargs)
        return TypeAdapter(list[SuiteResponse]).validate_python(data)

    def get_metric(
        self,
        id: str,
        rsid: str,
        locale: Optional[str] = None,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> MetricResponse:
        """Fetch a single metric by ID for the given report suite."""
        short_id = id.split("/")[-1] if "/" in id else id
        url = f"{self.api_endpoint}{AAEndpoints.METRICS}/{short_id}"

        params = kwargs.pop("params", {}) or {}
        params["rsid"] = rsid
        if locale is not None:
            params["locale"] = locale
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params
        metric = self.client._authenticated_request("get", url, **kwargs).json()
        return MetricResponse(**metric)

    def get_metrics(
        self,
        rsid: str,
        locale: Optional[str] = None,
        segmentable: Optional[bool] = None,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> list[MetricResponse]:
        """Fetch all metrics for the given report suite."""
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

    def get_dimension(
        self,
        id: str,
        rsid: str,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> DimensionResponse:
        """Fetch a single dimension by ID for the given report suite."""
        short_id = id.split("/")[-1] if "/" in id else id
        url = f"{self.api_endpoint}{AAEndpoints.DIMENSIONS}/{short_id}"

        params = kwargs.pop("params", {}) or {}
        params["rsid"] = rsid
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params
        data = self.client._authenticated_request("get", url, **kwargs).json()
        return DimensionResponse(**data)

    def get_dimensions(
        self,
        rsid: str,
        segmentable: Optional[bool] = None,
        reportable: Optional[bool] = None,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> list[DimensionResponse]:
        """Fetch all dimensions for the given report suite."""
        url = f"{self.api_endpoint}{AAEndpoints.DIMENSIONS}"

        params = kwargs.pop("params", {}) or {}
        params["rsid"] = rsid
        if segmentable is not None:
            params["segmentable"] = str(segmentable).lower()
        if reportable is not None:
            params["reportable"] = str(reportable).lower()
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params

        data = self.client._authenticated_request("get", url, **kwargs).json()
        return TypeAdapter(list[DimensionResponse]).validate_python(data)

    def get_calculated_metric(
        self,
        id: str,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> CalculatedMetricResponse:
        """Fetch a single calculated metric by ID."""
        url = f"{self.api_endpoint}{AAEndpoints.CALCULATED_METRICS}/{quote(id, safe='')}"

        params = kwargs.pop("params", {}) or {}
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params
        data = self.client._authenticated_request("get", url, **kwargs).json()
        return CalculatedMetricResponse(**data)

    def get_calculated_metrics(
        self,
        rsids: Optional[str] = None,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> list[CalculatedMetricResponse]:
        """Fetch all calculated metrics, optionally filtered by report suite."""
        url = f"{self.api_endpoint}{AAEndpoints.CALCULATED_METRICS}"

        params = kwargs.pop("params", {}) or {}
        if rsids is not None:
            params["rsids"] = rsids
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params

        data = self.client._paginated_request("get", url, **kwargs)
        return TypeAdapter(list[CalculatedMetricResponse]).validate_python(data)

    def get_segment(
        self,
        id: str,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> SegmentResponse:
        """Fetch a single segment by ID."""
        url = f"{self.api_endpoint}{AAEndpoints.SEGMENTS}/{quote(id, safe='')}"

        params = kwargs.pop("params", {}) or {}
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params
        data = self.client._authenticated_request("get", url, **kwargs).json()
        return SegmentResponse(**data)

    def get_segments(
        self,
        rsids: Optional[str] = None,
        expansion: Optional[str] = None,
        **kwargs,
    ) -> list[SegmentResponse]:
        """Fetch all segments, optionally filtered by report suite."""
        url = f"{self.api_endpoint}{AAEndpoints.SEGMENTS}"

        params = kwargs.pop("params", {}) or {}
        if rsids is not None:
            params["rsids"] = rsids
        if expansion is not None:
            params["expansion"] = expansion

        kwargs["params"] = params

        data = self.client._paginated_request("get", url, **kwargs)
        return TypeAdapter(list[SegmentResponse]).validate_python(data)

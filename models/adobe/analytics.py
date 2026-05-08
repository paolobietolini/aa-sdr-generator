from pydantic import BaseModel, Field
from typing import List, Optional, Union


class Company(BaseModel):
    """A single company (global report suite group) within an IMS organisation."""

    global_company_id: str = Field(alias="globalCompanyId")
    company_name: str = Field(alias="companyName")
    api_rate_policy: str = Field(alias="apiRateLimitPolicy")


class Organizations(BaseModel):
    """An IMS organisation and the companies it contains."""

    img_org_id: str = Field(alias="imsOrgId")
    companies: List[Company]


class DiscoveryResponse(BaseModel):
    """Response from the /discovery/me endpoint."""

    ims_user_id: str = Field(alias="imsUserId")
    ims_orgs: List[Organizations] = Field(alias="imsOrgs")


class SuiteResponse(BaseModel):
    """A report suite returned by the suites endpoint."""

    rsid: str
    id: str
    name: str
    parentRsid: Optional[str] = None
    currency: Optional[str] = None


class MetricResponse(BaseModel):
    """A standard or calculated metric returned by the metrics endpoint."""

    id: str
    title: Optional[str] = None
    name: Optional[str] = None
    type: Optional[Union[int, str]] = None
    category: Optional[str] = None
    calculated: Optional[Union[bool, str]] = None
    description: Optional[str] = None
    polarity: Optional[str] = None


class DimensionResponse(BaseModel):
    """A dimension returned by the dimensions endpoint."""

    id: str
    title: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    pathable: Optional[bool] = None
    segmentable: Optional[bool] = None
    reportable: Optional[List[str]] = None
    support: Optional[List[str]] = None
    tags: Optional[List[dict]] = None
    allowed_for_reporting: Optional[bool] = Field(default=None, alias="allowedForReporting")
    extra_title_info: Optional[str] = Field(default=None, alias="extraTitleInfo")


class CalculatedMetricDefinition(BaseModel):
    """Formula definition of a calculated metric."""

    formula: Optional[dict] = None
    func: Optional[str] = None
    version: Optional[List[int]] = None


class CalculatedMetricCompatibility(BaseModel):
    """Compatibility validation result for a calculated metric."""

    valid: Optional[bool] = None
    message: Optional[str] = None


class CalculatedMetricResponse(BaseModel):
    """A calculated metric returned by the calculatedmetrics endpoint."""

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    rsid: Optional[str] = None
    report_suite_name: Optional[str] = Field(default=None, alias="reportSuiteName")
    owner: Optional[dict] = None
    polarity: Optional[str] = None
    precision: Optional[int] = None
    type: Optional[str] = None
    definition: Optional[CalculatedMetricDefinition] = None
    compatibility: Optional[CalculatedMetricCompatibility] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[dict]] = None
    modified: Optional[str] = None
    created: Optional[str] = None


class SegmentDefinition(BaseModel):
    """Container definition of a segment."""

    container: Optional[dict] = None
    func: Optional[str] = None
    version: Optional[List[int]] = None


class SegmentCompatibility(BaseModel):
    """Compatibility validation result for a segment."""

    valid: Optional[bool] = None
    message: Optional[str] = None


class SegmentResponse(BaseModel):
    """A segment returned by the segments endpoint."""

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    rsid: Optional[str] = None
    report_suite_name: Optional[str] = Field(default=None, alias="reportSuiteName")
    owner: Optional[dict] = None
    definition: Optional[SegmentDefinition] = None
    compatibility: Optional[SegmentCompatibility] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[dict]] = None
    modified: Optional[str] = None
    created: Optional[str] = None

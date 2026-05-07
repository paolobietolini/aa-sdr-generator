from pydantic import BaseModel,Field
from typing import List, Optional, Union


class Company(BaseModel):
    global_company_id :str = Field(alias='globalCompanyId')
    company_name :str = Field(alias='companyName')
    api_rate_policy :str = Field(alias='apiRateLimitPolicy')

class Organizations(BaseModel):
    img_org_id :str = Field(alias='imsOrgId')
    companies: List[Company]

class DiscoveryResponse(BaseModel):
    ims_user_id : str = Field(alias='imsUserId')
    ims_orgs: List[Organizations] = Field(alias='imsOrgs')

class SuiteResponse(BaseModel):
    rsid: str
    id: str
    name: str
    parentRsid: Optional[str] = None
    currency: Optional[str] = None


class MetricResponse(BaseModel):
    id: str
    title: Optional[str] = None
    name: Optional[str] = None
    type: Optional[Union[int, str]] = None
    category: Optional[str] = None
    calculated: Optional[Union[bool, str]] = None
    description: Optional[str] = None
    polarity: Optional[str] = None


class DimensionResponse(BaseModel):
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
    formula: Optional[dict] = None
    func: Optional[str] = None
    version: Optional[List[int]] = None


class CalculatedMetricCompatibility(BaseModel):
    valid: Optional[bool] = None
    message: Optional[str] = None


class CalculatedMetricResponse(BaseModel):
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
    container: Optional[dict] = None
    func: Optional[str] = None
    version: Optional[List[int]] = None


class SegmentCompatibility(BaseModel):
    valid: Optional[bool] = None
    message: Optional[str] = None


class SegmentResponse(BaseModel):
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



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

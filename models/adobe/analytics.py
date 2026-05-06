from pydantic import BaseModel,Field
from typing import List


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
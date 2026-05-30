from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BrokerCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    short_name: str = Field(min_length=1, max_length=50)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: str = "active"
    business_status: str = "待对接"
    system_version: Optional[str] = None
    system_version_updated_at: Optional[str] = None
    system_version_content: Optional[str] = None
    note: Optional[str] = None


class BrokerUpdatePayload(BrokerCreatePayload):
    pass


class BrokerFeaturedUpdatePayload(BaseModel):
    broker_ids: List[int] = Field(default_factory=list)


class BrokerServerPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cpu: Optional[str] = None
    memory: Optional[str] = None
    operating_system: Optional[str] = None
    ip_address: Optional[str] = None
    remark: Optional[str] = None


class BrokerEntrustSitePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    client_type: str = Field(min_length=1, max_length=20)
    software_version: Optional[str] = None
    updated_at: Optional[str] = None
    operating_system: Optional[str] = None
    is_xinchuang: bool = False
    remark: Optional[str] = None

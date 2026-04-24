from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BrokerCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    short_name: str = Field(min_length=1, max_length=50)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: str = "active"
    note: Optional[str] = None


class BrokerUpdatePayload(BrokerCreatePayload):
    pass

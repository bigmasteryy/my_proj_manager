from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RiskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    level: str = Field(min_length=1, max_length=20)
    affects_milestone: bool = False
    owner_name: str = Field(min_length=1, max_length=50)
    planned_resolve_date: date
    status: str = "待处理"
    action_plan: str = Field(min_length=1)


class RiskStatusUpdatePayload(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    action_plan: str = Field(min_length=1)


class RiskUpdatePayload(RiskCreatePayload):
    pass

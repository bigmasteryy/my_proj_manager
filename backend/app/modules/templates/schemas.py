from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class TemplateTaskPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    planned_content: str = Field(min_length=1)
    default_owner_name: Optional[str] = None
    offset_days: int = 0


class TemplateRiskPayload(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    level: str = Field(min_length=1, max_length=20)
    affects_milestone: bool = False
    action_plan: str = Field(min_length=1)
    offset_days: int = 0


class TemplateCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    template_type: str = Field(min_length=1, max_length=50)
    scene: str = Field(min_length=1, max_length=200)
    tasks: List[TemplateTaskPayload]
    risks: List[TemplateRiskPayload]


class TemplateUpdatePayload(TemplateCreatePayload):
    pass


class TemplateGenerateProjectPayload(BaseModel):
    broker_id: int
    name: str = Field(min_length=1, max_length=100)
    owner_name: str = Field(min_length=1, max_length=50)
    planned_date: date
    status: str = "准备中"
    description: Optional[str] = None


class ProjectSaveAsTemplatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scene: str = Field(min_length=1, max_length=200)

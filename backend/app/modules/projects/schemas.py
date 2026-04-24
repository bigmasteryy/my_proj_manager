from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreatePayload(BaseModel):
    broker_id: int
    name: str = Field(min_length=1, max_length=100)
    project_type: str = Field(min_length=1, max_length=50)
    owner_name: str = Field(min_length=1, max_length=50)
    planned_date: date
    status: str = "准备中"
    description: Optional[str] = None


class ProjectUpdatePayload(ProjectCreatePayload):
    pass

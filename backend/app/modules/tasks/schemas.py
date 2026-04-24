from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    owner_name: str = Field(min_length=1, max_length=50)
    planned_content: str = Field(min_length=1)
    planned_date: date
    actual_action: Optional[str] = None
    completion_result: Optional[str] = None
    status: str = "未开始"


class TaskStatusUpdatePayload(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    actual_action: Optional[str] = None
    completion_result: Optional[str] = None


class TaskUpdatePayload(TaskCreatePayload):
    pass

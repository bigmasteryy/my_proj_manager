from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PersonalTaskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=20)
    priority: str = Field(min_length=1, max_length=20)
    note: Optional[str] = None
    planned_date: Optional[date] = None
    parent_task_id: Optional[int] = None


class PersonalTaskUpdatePayload(PersonalTaskCreatePayload):
    pass


class PersonalTaskCompletePayload(BaseModel):
    completion_result: str = Field(min_length=1, max_length=500)


class PersonalTaskSortPayload(BaseModel):
    ordered_ids: List[int]

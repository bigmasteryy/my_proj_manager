from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProgressValueUpdatePayload(BaseModel):
    status_value: Optional[str] = Field(default=None, max_length=30)
    current_num: Optional[int] = None
    target_num: Optional[int] = None
    bool_value: Optional[bool] = None
    text_value: Optional[str] = Field(default=None, max_length=500)
    is_na: bool = False
    remark: Optional[str] = None


class ProgressLogCreatePayload(BaseModel):
    item_template_id: Optional[int] = None
    log_date: datetime
    content: str = Field(min_length=1)
    progress_delta: int = 0
    progress_after: int = 0
    is_milestone: bool = False
    remark: Optional[str] = None


class ProgressRiskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    impact_desc: Optional[str] = None
    level: str = Field(min_length=1, max_length=20)
    owner_name: Optional[str] = Field(default=None, max_length=100)
    planned_resolve_date: Optional[date] = None
    status: str = Field(default="待处理", max_length=20)
    remark: Optional[str] = None


class ProgressRiskUpdatePayload(ProgressRiskCreatePayload):
    pass

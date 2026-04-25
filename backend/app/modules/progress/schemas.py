from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProgressProjectCreatePayload(BaseModel):
    code: Optional[str] = Field(default=None, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    project_type: str = Field(default="批量推进", min_length=1, max_length=50)
    description: Optional[str] = None
    status: str = Field(default="active", max_length=20)
    sort_no: Optional[int] = None


class ProgressProjectBrokerAddPayload(BaseModel):
    broker_ids: List[int] = Field(default_factory=list)
    input_mode: str = Field(default="明细", max_length=20)
    owner_name: Optional[str] = Field(default=None, max_length=100)
    remark: Optional[str] = None


class ProgressItemTemplateCreatePayload(BaseModel):
    item_key: Optional[str] = Field(default=None, max_length=50)
    item_label: str = Field(min_length=1, max_length=100)
    group_key: Optional[str] = Field(default=None, max_length=50)
    group_label: Optional[str] = Field(default=None, max_length=100)
    item_type: str = Field(default="status", max_length=30)
    weight: int = Field(default=0, ge=0, le=100)
    allow_na: bool = False
    sort_no: Optional[int] = None
    value_rule: Optional[str] = None
    remark: Optional[str] = None


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


class ProgressLogUpdatePayload(ProgressLogCreatePayload):
    pass


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


class ProgressStage2StepCreatePayload(BaseModel):
    step_no_display: str = Field(min_length=1, max_length=20)
    step_name: str = Field(min_length=1, max_length=255)
    owner_actual: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="未开始", min_length=1, max_length=20)
    remark: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ProgressStage2StepUpdatePayload(BaseModel):
    step_no_display: Optional[str] = Field(default=None, max_length=20)
    step_name: Optional[str] = Field(default=None, max_length=255)
    owner_actual: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(min_length=1, max_length=20)
    remark: Optional[str] = None
    blocker_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ProgressStage2StepMovePayload(BaseModel):
    direction: str = Field(min_length=1, max_length=10)

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BrokerIssueStatusPayload(BaseModel):
    broker_id: int
    is_affected: bool = True
    impact_desc: Optional[str] = None
    fix_status: str = Field(default="未开始", max_length=30)
    fix_version: Optional[str] = Field(default=None, max_length=100)
    released_at: Optional[datetime] = None
    verified_result: Optional[str] = None
    owner_name: Optional[str] = Field(default=None, max_length=100)
    remark: Optional[str] = None


class BrokerIssueCreatePayload(BaseModel):
    issue_type: str = Field(default="线上问题", max_length=20)
    title: str = Field(min_length=1, max_length=200)
    priority: str = Field(default="中", max_length=20)
    status: str = Field(default="待分析", max_length=30)
    description: Optional[str] = None
    impact_scope: Optional[str] = None
    planned_fix_version: Optional[str] = Field(default=None, max_length=100)
    solution: Optional[str] = None
    owner_name: Optional[str] = Field(default=None, max_length=100)
    planned_finish_date: Optional[date] = None
    remark: Optional[str] = None
    affected_brokers: List[BrokerIssueStatusPayload] = Field(default_factory=list)


class BrokerIssueUpdatePayload(BrokerIssueCreatePayload):
    pass


class BrokerIssueStatusUpdatePayload(BaseModel):
    is_affected: bool = True
    impact_desc: Optional[str] = None
    fix_status: str = Field(default="未开始", max_length=30)
    fix_version: Optional[str] = Field(default=None, max_length=100)
    released_at: Optional[datetime] = None
    verified_result: Optional[str] = None
    owner_name: Optional[str] = Field(default=None, max_length=100)
    remark: Optional[str] = None

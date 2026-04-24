from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectLogCreatePayload(BaseModel):
    content: str = Field(min_length=1)
    next_action: str = Field(min_length=1)


class ProjectLogUpdatePayload(ProjectLogCreatePayload):
    pass

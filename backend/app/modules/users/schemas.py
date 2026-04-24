from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreatePayload(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(min_length=1, max_length=20)
    status: str = Field(min_length=1, max_length=20)


class UserUpdatePayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=50)
    role: str = Field(min_length=1, max_length=20)
    status: str = Field(min_length=1, max_length=20)


class UserResetPasswordPayload(BaseModel):
    password: str = Field(min_length=6, max_length=100)

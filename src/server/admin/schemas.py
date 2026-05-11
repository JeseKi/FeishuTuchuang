# -*- coding: utf-8 -*-
"""
管理员用户管理 Pydantic 模型

公开接口：
- AdminUserOut
- AdminUserUpdate
"""

from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from src.server.auth.schemas import UserRole, UserStatus


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: Optional[str] = Field(default=None)
    role: UserRole
    status: UserStatus
    scope_overrides: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("scope_overrides_list"),
    )
    effective_scopes: list[str]
    available_scopes: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    password: str = Field(..., min_length=8)


class AdminUserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    password: Optional[str] = Field(default=None, min_length=8)


class AdminUserScopesUpdate(BaseModel):
    scopes: list[str] = Field(default_factory=list)

# -*- coding: utf-8 -*-
"""飞书文件夹接口模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeishuFolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    folder_token: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True

    @field_validator("name", "folder_token")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("不能为空")
        return normalized


class FeishuFolderCreate(FeishuFolderBase):
    pass


class FeishuFolderUpdate(FeishuFolderBase):
    pass


class FeishuFolderOut(BaseModel):
    id: int
    name: str
    folder_token: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

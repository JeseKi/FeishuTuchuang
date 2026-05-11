# -*- coding: utf-8 -*-
"""
示例模块 Pydantic 模型（模板版）

公开接口：
- `ItemCreate`、`ItemOut`
- `AsyncTaskCreate`、`AsyncTaskOut`、`AsyncTaskDetailOut`
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

TaskStatus = Literal["pending", "running", "completed", "failed"]
TaskLogLevel = Literal["info", "warning", "error"]
ASYNC_TASK_ID_PATTERN = r"^[A-Za-z0-9]{32}$"


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ItemOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class AsyncTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    total_count: int = Field(default=10, ge=1, le=200)
    fail_every: int = Field(default=0, ge=0, le=50)
    delay_ms: int = Field(default=300, ge=0, le=5000)


class AsyncTaskLogOut(BaseModel):
    id: int
    sequence: int
    level: TaskLogLevel
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AsyncTaskOut(BaseModel):
    id: str = Field(..., pattern=ASYNC_TASK_ID_PATTERN)
    name: str
    status: TaskStatus
    total_count: int
    processed_count: int
    success_count: int
    failure_count: int
    progress_percent: int
    fail_every: int
    delay_ms: int
    last_message: str | None
    requested_by_user_id: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AsyncTaskDetailOut(AsyncTaskOut):
    logs: list[AsyncTaskLogOut]


class ExampleExternalStatusOut(BaseModel):
    provider: str
    status: str
    message: str | None = None

# -*- coding: utf-8 -*-
"""
示例模块路由（模板版）

公开接口：
- GET /api/example/ping
- POST /api/example/items
- GET /api/example/items/{item_id}
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Security, status
from sqlalchemy.orm import Session

from src.server.database import get_db
from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from .schemas import (
    ASYNC_TASK_ID_PATTERN,
    AsyncTaskCreate,
    AsyncTaskDetailOut,
    AsyncTaskOut,
    ExampleExternalStatusOut,
    ItemCreate,
    ItemOut,
)
from . import service
from src.server.auth.service.scopes import SCOPE_PROFILE_READ
from src.server.dao.dao_base import run_in_thread

router = APIRouter(prefix="/api/example", tags=["示例"])


@router.get(
    "/ping",
    summary="健康检查",
    description="检查服务是否正常运行",
    response_description="返回服务状态信息",
    responses={
        200: {"description": "服务正常运行"},
    },
)
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.post(
    "/items",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
    description="创建一个新的项目，需要提供项目名称等基本信息。此接口需要用户登录。",
    response_description="返回新创建的项目信息",
    responses={
        201: {"description": "项目创建成功"},
        400: {"description": "请求参数错误"},
        401: {"description": "未授权访问"},
    },
)
async def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    def _create():
        return service.create_item(db, payload.name)

    return await run_in_thread(_create)


@router.get(
    "/items/{item_id}",
    response_model=ItemOut,
    summary="获取项目详情",
    description="根据项目ID获取指定项目的详细信息。此接口需要用户登录。",
    response_description="返回指定项目的详细信息",
    responses={
        200: {"description": "获取项目成功"},
        401: {"description": "未授权访问"},
        404: {"description": "项目不存在"},
    },
)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    def _get():
        return service.get_item(db, item_id)

    return await run_in_thread(_get)


@router.post(
    "/tasks",
    response_model=AsyncTaskOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="创建长时异步任务",
    description="创建一个示例长时任务，并在后台持续写入进度、日志和成功/失败统计。",
    response_description="返回新创建的任务概要",
)
async def create_async_task(
    payload: AsyncTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    def _create():
        task = service.create_async_task(db, payload, current_user)
        service.launch_async_task(db, task.id)
        return task

    return await run_in_thread(_create)


@router.get(
    "/tasks/{task_id}",
    response_model=AsyncTaskDetailOut,
    summary="获取异步任务详情",
    description="查询异步任务的当前进度、成功/失败统计及执行日志。",
    response_description="返回任务详情与日志列表",
)
async def get_async_task(
    task_id: Annotated[str, Path(pattern=ASYNC_TASK_ID_PATTERN)],
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    def _get():
        task, logs = service.get_async_task_detail(db, task_id)
        return AsyncTaskDetailOut.model_validate({**task.__dict__, "logs": logs})

    return await run_in_thread(_get)


@router.get(
    "/external/status",
    response_model=ExampleExternalStatusOut,
    summary="获取示例外部 API 状态",
    description="通过 provider 边界调用示例外部 API；测试环境默认使用 fake provider。",
    response_description="返回示例外部 API 状态",
)
async def get_external_status(
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    return await service.fetch_external_status()

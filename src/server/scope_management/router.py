# -*- coding: utf-8 -*-
"""
scope 分类管理路由
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_admin, get_current_admin_writer
from src.server.auth.models import User
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from . import service
from .schemas import ManagedScopeOut, ManagedScopeUpdate

router = APIRouter(prefix="/api/admin/scopes", tags=["Scope 管理"])


@router.get(
    "",
    response_model=list[ManagedScopeOut],
    summary="获取 scope 列表",
    description="管理员查看系统内所有已知 scope 及其分类",
    responses={
        200: {"description": "获取成功"},
        403: {"description": "无管理员权限"},
    },
)
async def list_managed_scopes(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    def _list():
        return service.list_scopes(db)

    return await run_in_thread(_list)


@router.patch(
    "/{scope}",
    response_model=ManagedScopeOut,
    summary="更新 scope 分类",
    description="管理员更新指定 scope 的分类，仅支持普通、敏感或危险",
    responses={
        200: {"description": "更新成功"},
        403: {"description": "无管理员权限"},
        404: {"description": "scope 不存在"},
    },
)
async def update_managed_scope(
    scope: str,
    payload: ManagedScopeUpdate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    def _update():
        return service.update_scope_category(db, scope, payload.category)

    return await run_in_thread(_update)

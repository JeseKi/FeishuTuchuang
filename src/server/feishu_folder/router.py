# -*- coding: utf-8 -*-
"""飞书文件夹管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_PROFILE_READ, SCOPE_PROFILE_WRITE
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from . import service
from .schemas import FeishuFolderCreate, FeishuFolderOut, FeishuFolderUpdate

router = APIRouter(prefix="/api/feishu/folders", tags=["飞书文件夹"])


@router.get(
    "",
    response_model=list[FeishuFolderOut],
    summary="列出飞书文件夹配置",
)
async def list_folders(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    return await run_in_thread(lambda: service.list_folders(db))


@router.get(
    "/active",
    response_model=FeishuFolderOut | None,
    summary="获取当前启用的飞书文件夹配置",
)
async def get_active_folder(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    return await run_in_thread(lambda: service.get_active_folder(db))


@router.post(
    "",
    response_model=FeishuFolderOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建飞书文件夹配置",
)
async def create_folder(
    payload: FeishuFolderCreate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    return await run_in_thread(lambda: service.create_folder(db, payload))


@router.put(
    "/{folder_id}",
    response_model=FeishuFolderOut,
    summary="更新飞书文件夹配置",
)
async def update_folder(
    folder_id: int,
    payload: FeishuFolderUpdate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    return await run_in_thread(
        lambda: service.update_folder(db, folder_id=folder_id, payload=payload)
    )


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除飞书文件夹配置",
)
async def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    await run_in_thread(lambda: service.delete_folder(db, folder_id=folder_id))

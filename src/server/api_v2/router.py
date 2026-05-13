# -*- coding: utf-8 -*-
"""外部集成 v2 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, Security, UploadFile, status
from sqlalchemy.orm import Session

from src.server.api_keys.dependencies import get_current_api_key_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_IMAGES_WRITE
from src.server.database import get_db
from src.server.feishu_folder import service as folder_service
from src.server.image_host import service as image_service
from src.server.image_host.schemas import ImageAssetOut

router = APIRouter(prefix="/api/v2", tags=["v2 API"])


@router.get(
    "/folders",
    response_model=list[str],
    summary="v2 API 获取可上传文件夹名称",
    description="返回可传给 v2 上传接口 folder_name 字段的文件夹名称列表。",
)
async def list_folder_names_v2(
    db: Session = Depends(get_db),
    _: User = Security(get_current_api_key_user, scopes=[SCOPE_IMAGES_WRITE]),
):
    return folder_service.list_folder_names(db)


@router.post(
    "/images",
    response_model=ImageAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="v2 API 上传图床图片",
    description=(
        "使用 X-API-Key 或 Authorization: Bearer <api_key> 上传图片，"
        "并通过 folder_name 指定飞书目标文件夹。"
    ),
)
async def upload_image_v2(
    request: Request,
    folder_name: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_api_key_user, scopes=[SCOPE_IMAGES_WRITE]),
):
    folder = folder_service.get_folder_by_name(db, folder_name)
    asset, reused_existing = await image_service.upload_image(
        db,
        upload=image,
        current_user=current_user,
        folder_token=folder.folder_token,
        feishu_folder_id=folder.id,
    )
    return image_service.to_output(request, asset, reused_existing)

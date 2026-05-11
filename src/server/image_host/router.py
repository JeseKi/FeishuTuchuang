# -*- coding: utf-8 -*-
"""图床路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, Security, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_PROFILE_READ
from src.server.database import get_db

from . import service
from .schemas import ImageAssetListOut, ImageAssetOut

router = APIRouter(tags=["图床"])


@router.get(
    "/api/images",
    response_model=ImageAssetListOut,
    summary="列出图床图片",
    description="按创建时间倒序列出本地数据库中的图床图片记录。",
)
async def list_images(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    assets = await service.list_images(db, limit=limit, offset=offset)
    return service.to_list_output(request, assets, limit=limit, offset=offset)


@router.post(
    "/api/images",
    response_model=ImageAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传图床图片",
    description="上传图片到飞书冷存储，同时写入本地缓存并返回本站图片 URL。",
)
async def upload_image(
    request: Request,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    asset, reused_existing = await service.upload_image(
        db,
        upload=image,
        current_user=current_user,
    )
    return service.to_output(request, asset, reused_existing)


@router.get(
    "/i/{filename}",
    summary="读取公开图片",
    description="公开读取图床图片；优先返回本地缓存，缺失时从飞书回源。",
)
async def get_public_image(
    filename: str,
    db: Session = Depends(get_db),
):
    cache_file, mime_type = await service.get_image_file(db, filename=filename)
    return FileResponse(
        cache_file,
        media_type=mime_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )

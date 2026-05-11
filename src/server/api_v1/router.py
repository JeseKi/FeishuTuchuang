# -*- coding: utf-8 -*-
"""外部集成 v1 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, Security, UploadFile, status
from sqlalchemy.orm import Session

from src.server.api_keys.dependencies import get_current_api_key_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_IMAGES_WRITE
from src.server.database import get_db
from src.server.image_host import service as image_service
from src.server.image_host.schemas import ImageAssetOut

router = APIRouter(prefix="/api/v1", tags=["v1 API"])


@router.post(
    "/images",
    response_model=ImageAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="v1 API 上传图床图片",
    description="使用 X-API-Key 或 Authorization: Bearer <api_key> 上传图片。",
)
async def upload_image_v1(
    request: Request,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_api_key_user, scopes=[SCOPE_IMAGES_WRITE]),
):
    asset, reused_existing = await image_service.upload_image(
        db,
        upload=image,
        current_user=current_user,
    )
    return image_service.to_output(request, asset, reused_existing)


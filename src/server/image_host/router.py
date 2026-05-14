# -*- coding: utf-8 -*-
"""图床路由。"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Request,
    Security,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_PROFILE_READ
from src.server.database import get_db

from . import oauth, service
from .schemas import (
    IMAGE_ASSET_ID_PATTERN,
    FeishuOAuthAuthorizeOut,
    FeishuOAuthStatusOut,
    ImageAssetListOut,
    ImageAssetMoveIn,
    ImageAssetOut,
)

router = APIRouter(tags=["图床"])


@router.get(
    "/api/images/feishu/oauth/status",
    response_model=FeishuOAuthStatusOut,
    summary="获取飞书 Drive 授权状态",
)
async def get_feishu_oauth_status(
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    return oauth.get_oauth_status()


@router.get(
    "/api/images/feishu/oauth/authorize",
    response_model=FeishuOAuthAuthorizeOut,
    summary="生成飞书 Drive 用户授权链接",
)
async def create_feishu_oauth_authorize_url(
    request: Request,
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    return oauth.create_authorize_url(request)


@router.get(
    "/api/images/feishu/oauth/callback",
    response_class=HTMLResponse,
    summary="飞书 Drive OAuth 回调",
)
async def feishu_oauth_callback(
    code: str,
    state: str | None = None,
):
    await oauth.handle_callback(code, state)
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'>"
        "<title>飞书授权完成</title>"
        "<body style='font-family: sans-serif; padding: 24px'>"
        "<h2>飞书 Drive 授权完成</h2>"
        "<p>现在可以关闭这个页面并返回图床管理页。</p>"
        "</body>"
    )


@router.get(
    "/api/images",
    response_model=ImageAssetListOut,
    summary="列出图床图片",
    description="按创建时间倒序列出本地数据库中的图床图片记录。",
)
async def list_images(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    uploaded_from: Annotated[date | None, Query()] = None,
    uploaded_to: Annotated[date | None, Query()] = None,
    folder_id: Annotated[int | None, Query(ge=1)] = None,
    feishu_file_token: Annotated[str | None, Query(max_length=255)] = None,
    filename: Annotated[str | None, Query(max_length=255)] = None,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    assets = await service.list_images(
        db,
        limit=limit,
        offset=offset,
        uploaded_from=uploaded_from,
        uploaded_to=uploaded_to,
        feishu_folder_id=folder_id,
        feishu_file_token=feishu_file_token,
        filename=filename,
    )
    total = await service.count_images(
        db,
        uploaded_from=uploaded_from,
        uploaded_to=uploaded_to,
        feishu_folder_id=folder_id,
        feishu_file_token=feishu_file_token,
        filename=filename,
    )
    return service.to_list_output(
        request,
        assets,
        limit=limit,
        offset=offset,
        total=total,
    )


@router.post(
    "/api/images",
    response_model=ImageAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传图床图片",
    description="上传图片到飞书冷存储，同时写入本地缓存并返回本站图片 URL。",
)
async def upload_image(
    request: Request,
    folder_id: Annotated[int | None, Form(ge=1)] = None,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    asset, reused_existing = await service.upload_image(
        db,
        upload=image,
        current_user=current_user,
        feishu_folder_id=folder_id,
    )
    return service.to_output(request, asset, reused_existing)


@router.delete(
    "/api/images/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除图床图片",
    description="删除飞书 Drive 文件、本地缓存和数据库记录。",
)
async def delete_image(
    asset_id: Annotated[str, Path(pattern=IMAGE_ASSET_ID_PATTERN)],
    delete_remote: Annotated[bool, Query()] = True,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    await service.delete_image_asset(db, asset_id=asset_id, delete_remote=delete_remote)


@router.patch(
    "/api/images/{asset_id}/folder",
    response_model=ImageAssetOut,
    summary="移动图床图片到其他飞书文件夹",
    description="将飞书 Drive 文件移动到指定文件夹，并同步更新本地图片记录。",
)
async def move_image(
    request: Request,
    asset_id: Annotated[str, Path(pattern=IMAGE_ASSET_ID_PATTERN)],
    payload: ImageAssetMoveIn,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
):
    asset = await service.move_image_asset(
        db,
        asset_id=asset_id,
        feishu_folder_id=payload.folder_id,
    )
    return service.to_output(request, asset, False)


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

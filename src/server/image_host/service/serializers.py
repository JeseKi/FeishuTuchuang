# -*- coding: utf-8 -*-
"""图床响应序列化。"""

from __future__ import annotations

from fastapi import Request

from src.server.config import global_config

from ..config import image_host_config
from ..models import ImageAsset


def build_public_url(request: Request, asset: ImageAsset) -> str:
    path = f"/i/{asset.id}.{asset.extension}"
    if image_host_config.public_base_url:
        return f"{image_host_config.public_base_url.rstrip('/')}{path}"
    if global_config.app_domain:
        return f"{global_config.app_domain.rstrip('/')}{path}"
    return str(request.base_url).rstrip("/") + path


def to_output(request: Request, asset: ImageAsset, reused_existing: bool) -> dict:
    filename = f"{asset.id}.{asset.extension}"
    return {
        "id": asset.id,
        "filename": filename,
        "url": build_public_url(request, asset),
        "feishu_file_token": asset.feishu_file_token,
        "feishu_download_url": build_feishu_download_url(asset),
        "feishu_folder_id": asset.feishu_folder_id,
        "feishu_folder_name": (
            asset.feishu_folder.name if asset.feishu_folder is not None else None
        ),
        "original_filename": asset.original_filename,
        "mime_type": asset.mime_type,
        "size_bytes": asset.size_bytes,
        "sha256": asset.sha256,
        "created_at": asset.created_at,
        "last_accessed_at": asset.last_accessed_at,
        "reused_existing": reused_existing,
    }


def to_list_output(
    request: Request,
    assets: list[ImageAsset],
    *,
    limit: int,
    offset: int,
    total: int,
) -> dict:
    return {
        "items": [to_output(request, asset, False) for asset in assets],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def build_feishu_download_url(asset: ImageAsset) -> str:
    base_url = image_host_config.feishu_api_base_url.rstrip("/")
    return f"{base_url}/drive/v1/files/{asset.feishu_file_token}/download"

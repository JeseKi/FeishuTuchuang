# -*- coding: utf-8 -*-
"""图床图片资产写入、读取与移动服务。"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.dao.dao_base import run_in_thread
from src.server.feishu_folder.service import get_folder_by_id

from ..dao import ImageAssetDAO
from ..models import ImageAsset
from ..storage import ImageStorageBackend, use_upload_folder_token
from .access import record_image_access
from .cache import build_cache_path, cache_root, ensure_cache_file, write_cache_file
from .constants import MIME_TO_EXTENSION
from .folders import resolve_upload_folder
from .validation import detect_mime_type, parse_public_filename, validate_size


async def upload_image(
    db: Session,
    *,
    upload: UploadFile,
    current_user: User,
    folder_token: str | None = None,
    feishu_folder_id: int | None = None,
) -> tuple[ImageAsset, bool]:
    content = await upload.read()
    validate_size(content)
    now = datetime.now(timezone.utc)
    upload_folder_token, upload_folder_id = await run_in_thread(
        lambda: resolve_upload_folder(db, folder_token, feishu_folder_id)
    )

    mime_type = detect_mime_type(content, upload.content_type)
    extension = MIME_TO_EXTENSION[mime_type]
    sha256 = hashlib.sha256(content).hexdigest()
    existing = await run_in_thread(lambda: ImageAssetDAO(db).get_by_sha256(sha256))
    if existing:
        ensure_cache_file(existing, content)
        record_image_access(existing.id, now)
        if not existing.feishu_file_token:
            file_token = await _put_image(
                folder_token=upload_folder_token,
                content=content,
                filename=f"{existing.id}.{extension}",
                mime_type=mime_type,
            )
            existing = await run_in_thread(
                lambda: ImageAssetDAO(db).update_drive_storage(
                    existing,
                    feishu_file_token=file_token,
                    extension=extension,
                    mime_type=mime_type,
                    size_bytes=len(content),
                    cache_path=str(build_cache_path(existing.id, extension)),
                    feishu_folder_id=upload_folder_id,
                    last_accessed_at=now,
                )
            )
        return existing, True

    asset_id = sha256[:32]
    cache_path = build_cache_path(asset_id, extension)
    filename = f"{asset_id}.{extension}"
    feishu_file_token = await _put_image(
        folder_token=upload_folder_token,
        content=content,
        filename=filename,
        mime_type=mime_type,
    )
    write_cache_file(cache_path, content)

    try:
        def _create_asset():
            return ImageAssetDAO(db).create(
                asset_id=asset_id,
                sha256=sha256,
                original_filename=upload.filename or filename,
                extension=extension,
                mime_type=mime_type,
                size_bytes=len(content),
                feishu_file_token=feishu_file_token,
                feishu_folder_id=upload_folder_id,
                cache_path=str(cache_path),
                uploaded_by_user_id=current_user.id,
                last_accessed_at=now,
            )

        asset = await run_in_thread(_create_asset)
    except IntegrityError:
        db.rollback()
        asset = await run_in_thread(lambda: ImageAssetDAO(db).get_by_sha256(sha256))
        if not asset:
            raise
        return asset, True

    return asset, False


async def get_image_file(db: Session, *, filename: str) -> tuple[Path, str]:
    asset_id, extension = parse_public_filename(filename)
    asset = await run_in_thread(lambda: ImageAssetDAO(db).get(asset_id))
    if not asset or asset.extension != extension:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not asset.feishu_file_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    record_image_access(asset.id)

    cache_file = cache_root() / asset.cache_path
    if cache_file.exists():
        return cache_file, asset.mime_type

    content = await _get_storage_backend().get_image(asset.feishu_file_token)
    write_cache_file(Path(asset.cache_path), content)
    return cache_root() / asset.cache_path, asset.mime_type


async def delete_image_asset(
    db: Session,
    *,
    asset_id: str,
    delete_remote: bool = True,
) -> None:
    asset = await run_in_thread(lambda: ImageAssetDAO(db).get(asset_id))
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not asset.feishu_file_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    if delete_remote:
        await _get_storage_backend().delete_image(asset.feishu_file_token)

    cache_file = cache_root() / asset.cache_path
    if cache_file.exists() and cache_file.is_file():
        cache_file.unlink()

    await run_in_thread(lambda: ImageAssetDAO(db).delete(asset))


async def move_image_asset(
    db: Session,
    *,
    asset_id: str,
    feishu_folder_id: int,
) -> ImageAsset:
    asset = await run_in_thread(lambda: ImageAssetDAO(db).get(asset_id))
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not asset.feishu_file_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    folder = await run_in_thread(lambda: get_folder_by_id(db, feishu_folder_id))
    if asset.feishu_folder_id == folder.id:
        return asset

    await _get_storage_backend().move_image(
        asset.feishu_file_token,
        folder_token=folder.folder_token,
    )
    return await run_in_thread(
        lambda: ImageAssetDAO(db).update_folder(
            asset,
            feishu_folder_id=folder.id,
        )
    )


async def _put_image(
    *,
    folder_token: str | None,
    content: bytes,
    filename: str,
    mime_type: str,
) -> str:
    with use_upload_folder_token(folder_token):
        return await _get_storage_backend().put_image(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )


def _get_storage_backend() -> ImageStorageBackend:
    from src.server.image_host import service as image_host_service

    return image_host_service.get_storage_backend()

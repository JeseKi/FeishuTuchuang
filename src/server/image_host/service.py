# -*- coding: utf-8 -*-
"""图床业务服务。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from threading import Lock
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.config import global_config
from src.server.dao.dao_base import run_in_thread
from src.server.feishu_folder.service import get_active_folder, get_folder_by_id

from .config import image_host_config
from .dao import ImageAssetDAO
from .models import ImageAsset
from .storage import get_storage_backend, use_upload_folder_token

MIME_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/x-icon": "ico",
    "image/vnd.microsoft.icon": "ico",
    "image/tiff": "tiff",
    "image/heic": "heic",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/ogg": "ogv",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
    "video/mpeg": "mpeg",
}

MAGIC_MIME = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
    (b"\x00\x00\x01\x00", "image/x-icon"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"\x1aE\xdf\xa3", "video/webm"),
    (b"OggS", "video/ogg"),
)
MAX_HEIC_BRAND_SCAN_BYTES = 32
MAX_MP4_BRAND_SCAN_BYTES = 32
_pending_access_times: dict[str, datetime] = {}
_pending_access_lock = Lock()


async def upload_image(
    db: Session,
    *,
    upload: UploadFile,
    current_user: User,
    folder_token: str | None = None,
    feishu_folder_id: int | None = None,
) -> tuple[ImageAsset, bool]:
    content = await upload.read()
    _validate_size(content)
    now = datetime.now(timezone.utc)
    upload_folder_token, upload_folder_id = await run_in_thread(
        lambda: _resolve_upload_folder(db, folder_token, feishu_folder_id)
    )

    mime_type = _detect_mime_type(content, upload.content_type)
    extension = MIME_TO_EXTENSION[mime_type]
    sha256 = hashlib.sha256(content).hexdigest()
    existing = await run_in_thread(lambda: ImageAssetDAO(db).get_by_sha256(sha256))
    if existing:
        _ensure_cache_file(existing, content)
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
                    cache_path=str(_build_cache_path(existing.id, extension)),
                    feishu_folder_id=upload_folder_id,
                    last_accessed_at=now,
                )
            )
        return existing, True

    asset_id = sha256[:32]
    cache_path = _build_cache_path(asset_id, extension)
    filename = f"{asset_id}.{extension}"
    feishu_file_token = await _put_image(
        folder_token=upload_folder_token,
        content=content,
        filename=filename,
        mime_type=mime_type,
    )
    _write_cache_file(cache_path, content)

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
    asset_id, extension = _parse_public_filename(filename)
    asset = await run_in_thread(lambda: ImageAssetDAO(db).get(asset_id))
    if not asset or asset.extension != extension:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    if not asset.feishu_file_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    record_image_access(asset.id)

    cache_file = _cache_root() / asset.cache_path
    if cache_file.exists():
        return cache_file, asset.mime_type

    content = await get_storage_backend().get_image(asset.feishu_file_token)
    _write_cache_file(Path(asset.cache_path), content)
    return _cache_root() / asset.cache_path, asset.mime_type


async def list_images(
    db: Session,
    *,
    limit: int,
    offset: int,
    uploaded_from: date | None = None,
    uploaded_to: date | None = None,
    feishu_folder_id: int | None = None,
    feishu_file_token: str | None = None,
    filename: str | None = None,
) -> list[ImageAsset]:
    created_at_from, created_at_before = _build_created_at_bounds(
        uploaded_from,
        uploaded_to,
    )
    normalized_feishu_file_token = _normalize_search_value(feishu_file_token)
    normalized_filename = _normalize_search_value(filename)
    return await run_in_thread(
        lambda: ImageAssetDAO(db).list_assets(
            limit=limit,
            offset=offset,
            created_at_from=created_at_from,
            created_at_before=created_at_before,
            feishu_folder_id=feishu_folder_id,
            feishu_file_token=normalized_feishu_file_token,
            filename=normalized_filename,
        )
    )


async def count_images(
    db: Session,
    *,
    uploaded_from: date | None = None,
    uploaded_to: date | None = None,
    feishu_folder_id: int | None = None,
    feishu_file_token: str | None = None,
    filename: str | None = None,
) -> int:
    created_at_from, created_at_before = _build_created_at_bounds(
        uploaded_from,
        uploaded_to,
    )
    normalized_feishu_file_token = _normalize_search_value(feishu_file_token)
    normalized_filename = _normalize_search_value(filename)
    return await run_in_thread(
        lambda: ImageAssetDAO(db).count_assets(
            created_at_from=created_at_from,
            created_at_before=created_at_before,
            feishu_folder_id=feishu_folder_id,
            feishu_file_token=normalized_feishu_file_token,
            filename=normalized_filename,
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
        return await get_storage_backend().put_image(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )


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
        await get_storage_backend().delete_image(asset.feishu_file_token)

    cache_file = _cache_root() / asset.cache_path
    if cache_file.exists() and cache_file.is_file():
        cache_file.unlink()

    await run_in_thread(lambda: ImageAssetDAO(db).delete(asset))


def record_image_access(
    asset_id: str,
    accessed_at: datetime | None = None,
) -> None:
    if accessed_at is None:
        accessed_at = datetime.now(timezone.utc)
    with _pending_access_lock:
        current = _pending_access_times.get(asset_id)
        if current is None or accessed_at > current:
            _pending_access_times[asset_id] = accessed_at


def flush_pending_image_accesses(db: Session) -> int:
    with _pending_access_lock:
        snapshot = dict(_pending_access_times)
    if not snapshot:
        return 0

    updated_count = ImageAssetDAO(db).update_last_accessed_at(snapshot)
    with _pending_access_lock:
        for asset_id, flushed_at in snapshot.items():
            if _pending_access_times.get(asset_id) == flushed_at:
                del _pending_access_times[asset_id]
    return updated_count


def cleanup_expired_cache_files(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=image_host_config.cache_ttl_hours)
    stale_assets = ImageAssetDAO(db).list_stale_cache_assets(cutoff)
    deleted_count = 0
    cache_root = _cache_root()
    for asset in stale_assets:
        cache_file = cache_root / asset.cache_path
        if cache_file.exists() and cache_file.is_file():
            cache_file.unlink()
            deleted_count += 1
    return deleted_count


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
        "feishu_download_url": _build_feishu_download_url(asset),
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


def _build_feishu_download_url(asset: ImageAsset) -> str:
    base_url = image_host_config.feishu_api_base_url.rstrip("/")
    return f"{base_url}/drive/v1/files/{asset.feishu_file_token}/download"


def _resolve_upload_folder(
    db: Session,
    folder_token: str | None,
    feishu_folder_id: int | None,
) -> tuple[str | None, int | None]:
    if folder_token is not None:
        return folder_token, feishu_folder_id

    if feishu_folder_id is not None:
        folder = get_folder_by_id(db, feishu_folder_id)
        return folder.folder_token, folder.id

    folder = get_active_folder(db)
    if folder is None:
        return None, None
    return folder.folder_token, folder.id


def _build_created_at_bounds(
    uploaded_from: date | None,
    uploaded_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    created_at_from = None
    created_at_before = None
    if uploaded_from is not None:
        created_at_from = datetime.combine(uploaded_from, time.min, timezone.utc)
    if uploaded_to is not None:
        next_day = uploaded_to + timedelta(days=1)
        created_at_before = datetime.combine(next_day, time.min, timezone.utc)
    return created_at_from, created_at_before


def _normalize_search_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_size(content: bytes) -> None:
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件不能为空",
        )
    max_bytes = image_host_config.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件不能超过 {image_host_config.max_upload_mb}MB",
        )


def _detect_mime_type(content: bytes, declared_mime: str | None) -> str:
    detected = None
    for prefix, mime_type in MAGIC_MIME:
        if content.startswith(prefix):
            detected = mime_type
            break

    if detected is None and _looks_like_webp(content):
        detected = "image/webp"
    if detected is None and _looks_like_heic(content):
        detected = "image/heic"
    if detected is None:
        detected = _detect_iso_video_mime_type(content)
    if detected is None and _looks_like_avi(content):
        detected = "video/x-msvideo"

    mime_type = detected or (declared_mime or "").split(";")[0].strip().lower()
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    if mime_type == "video/ogv":
        mime_type = "video/ogg"
    if mime_type not in MIME_TO_EXTENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持常见图片和视频文件",
        )
    return mime_type


def _looks_like_webp(content: bytes) -> bool:
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"


def _looks_like_heic(content: bytes) -> bool:
    brands = (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1")
    return len(content) >= 12 and b"ftyp" in content[:MAX_HEIC_BRAND_SCAN_BYTES] and any(
        brand in content[:MAX_HEIC_BRAND_SCAN_BYTES] for brand in brands
    )


def _detect_iso_video_mime_type(content: bytes) -> str | None:
    brands = (b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"m4v ", b"qt  ")
    if not (
        len(content) >= 12
        and content[4:8] == b"ftyp"
        and any(brand in content[:MAX_MP4_BRAND_SCAN_BYTES] for brand in brands)
    ):
        return None
    if b"qt  " in content[:MAX_MP4_BRAND_SCAN_BYTES]:
        return "video/quicktime"
    return "video/mp4"


def _looks_like_avi(content: bytes) -> bool:
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"AVI "


def _parse_public_filename(filename: str) -> tuple[str, str]:
    if "." not in filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    asset_id, extension = filename.rsplit(".", 1)
    if len(asset_id) != 32 or not all(char in "0123456789abcdef" for char in asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    extension = extension.lower()
    if extension not in set(MIME_TO_EXTENSION.values()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    return asset_id, extension


def _build_cache_path(asset_id: str, extension: str) -> Path:
    return Path(asset_id[:2]) / f"{asset_id}.{extension}"


def _cache_root() -> Path:
    root = image_host_config.cache_dir
    if not root.is_absolute():
        root = Path(global_config.project_root) / root
    return root


def _write_cache_file(relative_path: Path, content: bytes) -> None:
    cache_file = _cache_root() / relative_path
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(content)


def _ensure_cache_file(asset: ImageAsset, content: bytes) -> None:
    cache_file = _cache_root() / asset.cache_path
    if not cache_file.exists():
        _write_cache_file(Path(asset.cache_path), content)

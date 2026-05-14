# -*- coding: utf-8 -*-
"""图床访问时间与缓存清理服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock

from sqlalchemy.orm import Session

from ..config import image_host_config
from ..dao import ImageAssetDAO
from .cache import cache_root

_pending_access_times: dict[str, datetime] = {}
_pending_access_lock = Lock()


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
    root = cache_root()
    for asset in stale_assets:
        cache_file = root / asset.cache_path
        if cache_file.exists() and cache_file.is_file():
            cache_file.unlink()
            deleted_count += 1
    return deleted_count

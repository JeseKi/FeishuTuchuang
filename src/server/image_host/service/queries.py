# -*- coding: utf-8 -*-
"""图床图片查询服务。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from src.server.dao.dao_base import run_in_thread

from ..dao import ImageAssetDAO
from ..models import ImageAsset


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
    created_at_from, created_at_before = build_created_at_bounds(
        uploaded_from,
        uploaded_to,
    )
    normalized_feishu_file_token = normalize_search_value(feishu_file_token)
    normalized_filename = normalize_search_value(filename)
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
    created_at_from, created_at_before = build_created_at_bounds(
        uploaded_from,
        uploaded_to,
    )
    normalized_feishu_file_token = normalize_search_value(feishu_file_token)
    normalized_filename = normalize_search_value(filename)
    return await run_in_thread(
        lambda: ImageAssetDAO(db).count_assets(
            created_at_from=created_at_from,
            created_at_before=created_at_before,
            feishu_folder_id=feishu_folder_id,
            feishu_file_token=normalized_feishu_file_token,
            filename=normalized_filename,
        )
    )


def build_created_at_bounds(
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


def normalize_search_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None

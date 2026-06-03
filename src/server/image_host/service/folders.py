# -*- coding: utf-8 -*-
"""图床上传目标文件夹解析。"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.dao.dao_base import run_in_thread
from src.server.feishu_folder.service import get_active_folder, get_folder_by_id

from ..dao import ImageHostFeishuFolderBucketDAO
from ..models import ImageHostFeishuFolderBucket
from ..storage import ImageStorageBackend

MAX_FOLDER_NODE_COUNT = 1500
BUCKET_NAME_PREFIX = "image-host-bucket"


@dataclass(frozen=True)
class UploadFolderTarget:
    folder_token: str | None
    feishu_folder_id: int | None
    feishu_folder_bucket_id: int | None


async def resolve_upload_folder(
    db: Session,
    folder_token: str | None,
    feishu_folder_id: int | None,
    storage: ImageStorageBackend,
) -> UploadFolderTarget:
    resolved_folder_token, resolved_folder_id = await resolve_logical_upload_folder(
        db,
        folder_token,
        feishu_folder_id,
    )
    if resolved_folder_token is None or resolved_folder_id is None:
        return UploadFolderTarget(
            folder_token=resolved_folder_token,
            feishu_folder_id=resolved_folder_id,
            feishu_folder_bucket_id=None,
        )

    bucket = await reserve_upload_folder_bucket(
        db,
        storage=storage,
        feishu_folder_id=resolved_folder_id,
        parent_folder_token=resolved_folder_token,
    )
    return UploadFolderTarget(
        folder_token=bucket.folder_token,
        feishu_folder_id=resolved_folder_id,
        feishu_folder_bucket_id=bucket.id,
    )


async def resolve_logical_upload_folder(
    db: Session,
    folder_token: str | None,
    feishu_folder_id: int | None,
) -> tuple[str | None, int | None]:
    return await run_in_thread(
        lambda: _resolve_logical_upload_folder(db, folder_token, feishu_folder_id)
    )


def _resolve_logical_upload_folder(
    db: Session,
    folder_token: str | None,
    feishu_folder_id: int | None,
) -> tuple[str | None, int | None]:
    if folder_token is not None:
        return folder_token, feishu_folder_id

    if feishu_folder_id is not None:
        folder = get_folder_by_id(db, feishu_folder_id)
        return folder.folder_token, folder.id

    active_folder = get_active_folder(db)
    if active_folder is None:
        return None, None
    return active_folder.folder_token, active_folder.id


async def reserve_upload_folder_bucket(
    db: Session,
    *,
    storage: ImageStorageBackend,
    feishu_folder_id: int,
    parent_folder_token: str,
) -> ImageHostFeishuFolderBucket:
    available_bucket = await run_in_thread(
        lambda: ImageHostFeishuFolderBucketDAO(db).get_available(
            feishu_folder_id=feishu_folder_id,
            max_assigned_count=MAX_FOLDER_NODE_COUNT,
        )
    )
    if available_bucket is not None:
        return await run_in_thread(
            lambda: ImageHostFeishuFolderBucketDAO(db).increment_assigned_count(
                available_bucket
            )
        )

    latest_bucket = await run_in_thread(
        lambda: ImageHostFeishuFolderBucketDAO(db).get_latest(
            feishu_folder_id=feishu_folder_id
        )
    )
    if latest_bucket is not None:
        remote_node_count = await storage.count_folder_nodes(
            folder_token=latest_bucket.folder_token
        )
        if remote_node_count < MAX_FOLDER_NODE_COUNT:
            calibrated_bucket = await run_in_thread(
                lambda: ImageHostFeishuFolderBucketDAO(db).update_assigned_count(
                    latest_bucket,
                    assigned_count=remote_node_count,
                )
            )
            return await run_in_thread(
                lambda: ImageHostFeishuFolderBucketDAO(db).increment_assigned_count(
                    calibrated_bucket
                )
            )

    parent_node_count = await storage.count_folder_nodes(folder_token=parent_folder_token)
    if parent_node_count >= MAX_FOLDER_NODE_COUNT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="飞书主文件夹节点已满，无法创建新的自动子文件夹",
        )

    sequence = latest_bucket.sequence + 1 if latest_bucket is not None else 1
    bucket_name = _build_bucket_name(sequence)
    bucket_token = await storage.create_folder(
        parent_folder_token=parent_folder_token,
        name=bucket_name,
    )
    return await run_in_thread(
        lambda: ImageHostFeishuFolderBucketDAO(db).create(
            feishu_folder_id=feishu_folder_id,
            name=bucket_name,
            folder_token=bucket_token,
            sequence=sequence,
            assigned_count=1,
        )
    )


async def release_upload_folder_bucket(
    db: Session,
    *,
    feishu_folder_bucket_id: int | None,
) -> None:
    await run_in_thread(
        lambda: ImageHostFeishuFolderBucketDAO(db).decrement_assigned_count(
            feishu_folder_bucket_id
        )
    )


def _build_bucket_name(sequence: int) -> str:
    return f"{BUCKET_NAME_PREFIX}-{sequence:04d}"

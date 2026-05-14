# -*- coding: utf-8 -*-
"""图床上传目标文件夹解析。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.feishu_folder.service import get_active_folder, get_folder_by_id


def resolve_upload_folder(
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

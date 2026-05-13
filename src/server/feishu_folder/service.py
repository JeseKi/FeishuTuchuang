# -*- coding: utf-8 -*-
"""飞书文件夹业务服务。"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .dao import FeishuFolderDAO
from .models import FeishuFolder
from .schemas import FeishuFolderCreate, FeishuFolderUpdate


def list_folders(db: Session) -> list[FeishuFolder]:
    return FeishuFolderDAO(db).list()


def get_active_folder(db: Session) -> FeishuFolder | None:
    return FeishuFolderDAO(db).get_active()


def get_active_folder_token(db: Session) -> str | None:
    folder = get_active_folder(db)
    if folder is None:
        return None
    return folder.folder_token


def create_folder(db: Session, payload: FeishuFolderCreate) -> FeishuFolder:
    dao = FeishuFolderDAO(db)
    try:
        return dao.create(
            name=payload.name,
            folder_token=payload.folder_token,
            is_active=payload.is_active,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹 token 已存在",
        )


def update_folder(
    db: Session,
    *,
    folder_id: int,
    payload: FeishuFolderUpdate,
) -> FeishuFolder:
    dao = FeishuFolderDAO(db)
    folder = dao.get(folder_id)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")

    existing = dao.get_by_token(payload.folder_token)
    if existing is not None and existing.id != folder.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹 token 已存在",
        )

    try:
        return dao.update(
            folder,
            name=payload.name,
            folder_token=payload.folder_token,
            is_active=payload.is_active,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹 token 已存在",
        )


def delete_folder(db: Session, *, folder_id: int) -> None:
    dao = FeishuFolderDAO(db)
    folder = dao.get(folder_id)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")
    dao.delete(folder)

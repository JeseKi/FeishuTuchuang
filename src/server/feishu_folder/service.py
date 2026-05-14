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
    return FeishuFolderDAO(db).list_all()


def list_folder_names(db: Session) -> list[str]:
    return FeishuFolderDAO(db).list_names()


def get_active_folder(db: Session) -> FeishuFolder | None:
    return FeishuFolderDAO(db).get_active()


def get_folder_by_id(db: Session, folder_id: int) -> FeishuFolder:
    folder = FeishuFolderDAO(db).get(folder_id)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")
    return folder


def get_folder_by_name(db: Session, folder_name: str) -> FeishuFolder:
    normalized_name = folder_name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹名称不能为空",
        )

    folder = FeishuFolderDAO(db).get_by_name(normalized_name)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")
    return folder


def get_active_folder_token(db: Session) -> str | None:
    folder = get_active_folder(db)
    if folder is None:
        return None
    return folder.folder_token


def create_folder(db: Session, payload: FeishuFolderCreate) -> FeishuFolder:
    dao = FeishuFolderDAO(db)
    _ensure_unique_folder_values(dao, name=payload.name, folder_token=payload.folder_token)
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

    _ensure_unique_folder_values(
        dao,
        name=payload.name,
        folder_token=payload.folder_token,
        exclude_id=folder.id,
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


def _ensure_unique_folder_values(
    dao: FeishuFolderDAO,
    *,
    name: str,
    folder_token: str,
    exclude_id: int | None = None,
) -> None:
    existing_name = dao.get_by_name(name)
    if existing_name is not None and existing_name.id != exclude_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹名称已存在",
        )

    existing_token = dao.get_by_token(folder_token)
    if existing_token is not None and existing_token.id != exclude_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹 token 已存在",
        )

# -*- coding: utf-8 -*-
"""飞书文件夹 DAO。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import FeishuFolder


class FeishuFolderDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, *, name: str, folder_token: str, is_active: bool) -> FeishuFolder:
        if is_active:
            self.deactivate_all(commit=False)
        folder = FeishuFolder(
            name=name,
            folder_token=folder_token,
            is_active=is_active,
        )
        self.db_session.add(folder)
        self.db_session.commit()
        self.db_session.refresh(folder)
        return folder

    def get(self, folder_id: int) -> FeishuFolder | None:
        return (
            self.db_session.query(FeishuFolder)
            .filter(FeishuFolder.id == folder_id)
            .first()
        )

    def get_by_token(self, folder_token: str) -> FeishuFolder | None:
        return (
            self.db_session.query(FeishuFolder)
            .filter(FeishuFolder.folder_token == folder_token)
            .first()
        )

    def get_active(self) -> FeishuFolder | None:
        return (
            self.db_session.query(FeishuFolder)
            .filter(FeishuFolder.is_active.is_(True))
            .order_by(FeishuFolder.updated_at.desc(), FeishuFolder.id.desc())
            .first()
        )

    def list(self) -> list[FeishuFolder]:
        return (
            self.db_session.query(FeishuFolder)
            .order_by(FeishuFolder.is_active.desc(), FeishuFolder.created_at.desc())
            .all()
        )

    def update(
        self,
        folder: FeishuFolder,
        *,
        name: str,
        folder_token: str,
        is_active: bool,
    ) -> FeishuFolder:
        if is_active:
            self.deactivate_all(commit=False)
        folder.name = name
        folder.folder_token = folder_token
        folder.is_active = is_active
        folder.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(folder)
        return folder

    def delete(self, folder: FeishuFolder) -> None:
        self.db_session.delete(folder)
        self.db_session.commit()

    def deactivate_all(self, *, commit: bool = True) -> None:
        self.db_session.query(FeishuFolder).update(
            {
                FeishuFolder.is_active: False,
                FeishuFolder.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
        if commit:
            self.db_session.commit()

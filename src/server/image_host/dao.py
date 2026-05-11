# -*- coding: utf-8 -*-
"""图床 DAO。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import ImageAsset


class ImageAssetDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(
        self,
        *,
        asset_id: str,
        sha256: str,
        original_filename: str,
        extension: str,
        mime_type: str,
        size_bytes: int,
        feishu_image_key: str,
        cache_path: str,
        uploaded_by_user_id: int | None,
    ) -> ImageAsset:
        asset = ImageAsset(
            id=asset_id,
            sha256=sha256,
            original_filename=original_filename,
            extension=extension,
            mime_type=mime_type,
            size_bytes=size_bytes,
            feishu_image_key=feishu_image_key,
            cache_path=cache_path,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self.db_session.add(asset)
        self.db_session.commit()
        self.db_session.refresh(asset)
        return asset

    def get(self, asset_id: str) -> ImageAsset | None:
        return (
            self.db_session.query(ImageAsset)
            .filter(ImageAsset.id == asset_id)
            .first()
        )

    def get_by_sha256(self, sha256: str) -> ImageAsset | None:
        return (
            self.db_session.query(ImageAsset)
            .filter(ImageAsset.sha256 == sha256)
            .first()
        )

    def list(self, *, limit: int, offset: int) -> list[ImageAsset]:
        return (
            self.db_session.query(ImageAsset)
            .order_by(ImageAsset.created_at.desc(), ImageAsset.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

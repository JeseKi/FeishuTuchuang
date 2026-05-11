# -*- coding: utf-8 -*-
"""图床 DAO。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import ImageAsset, ImageHostFeishuOAuthToken

FEISHU_OAUTH_TOKEN_ID = 1


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
        feishu_file_token: str,
        cache_path: str,
        uploaded_by_user_id: int | None,
        last_accessed_at: datetime,
    ) -> ImageAsset:
        asset = ImageAsset(
            id=asset_id,
            sha256=sha256,
            original_filename=original_filename,
            extension=extension,
            mime_type=mime_type,
            size_bytes=size_bytes,
            feishu_file_token=feishu_file_token,
            cache_path=cache_path,
            uploaded_by_user_id=uploaded_by_user_id,
            last_accessed_at=last_accessed_at,
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

    def delete(self, asset: ImageAsset) -> None:
        self.db_session.delete(asset)
        self.db_session.commit()

    def update_drive_storage(
        self,
        asset: ImageAsset,
        *,
        feishu_file_token: str,
        extension: str,
        mime_type: str,
        size_bytes: int,
        cache_path: str,
        last_accessed_at: datetime,
    ) -> ImageAsset:
        asset.feishu_file_token = feishu_file_token
        asset.extension = extension
        asset.mime_type = mime_type
        asset.size_bytes = size_bytes
        asset.cache_path = cache_path
        asset.last_accessed_at = last_accessed_at
        asset.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(asset)
        return asset

    def list_assets(self, *, limit: int, offset: int) -> list[ImageAsset]:
        return (
            self.db_session.query(ImageAsset)
            .filter(ImageAsset.feishu_file_token.is_not(None))
            .order_by(ImageAsset.created_at.desc(), ImageAsset.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_assets(self) -> int:
        return (
            self.db_session.query(ImageAsset)
            .filter(ImageAsset.feishu_file_token.is_not(None))
            .count()
        )

    def update_last_accessed_at(self, access_times: dict[str, datetime]) -> int:
        updated_count = 0
        for asset_id, accessed_at in access_times.items():
            updated_count += (
                self.db_session.query(ImageAsset)
                .filter(ImageAsset.id == asset_id)
                .update(
                    {
                        ImageAsset.last_accessed_at: accessed_at,
                        ImageAsset.updated_at: datetime.now(accessed_at.tzinfo),
                    },
                    synchronize_session=False,
                )
            )
        self.db_session.commit()
        return updated_count

    def list_stale_cache_assets(self, cutoff: datetime) -> list[ImageAsset]:
        return (
            self.db_session.query(ImageAsset)
            .filter(
                or_(
                    ImageAsset.last_accessed_at.is_(None),
                    ImageAsset.last_accessed_at < cutoff,
                )
            )
            .all()
        )


class FeishuOAuthTokenDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get(self) -> ImageHostFeishuOAuthToken | None:
        return (
            self.db_session.query(ImageHostFeishuOAuthToken)
            .filter(ImageHostFeishuOAuthToken.id == FEISHU_OAUTH_TOKEN_ID)
            .first()
        )

    def upsert(
        self,
        *,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        refresh_expires_at: datetime | None,
        open_id: str | None,
        union_id: str | None,
        user_id: str | None,
        connected_by_user_id: int | None = None,
    ) -> ImageHostFeishuOAuthToken:
        token = self.get()
        if token is None:
            token = ImageHostFeishuOAuthToken(
                id=FEISHU_OAUTH_TOKEN_ID,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                refresh_expires_at=refresh_expires_at,
                open_id=open_id,
                union_id=union_id,
                user_id=user_id,
                connected_by_user_id=connected_by_user_id,
            )
            self.db_session.add(token)
        else:
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.expires_at = expires_at
            token.refresh_expires_at = refresh_expires_at
            token.open_id = open_id
            token.union_id = union_id
            token.user_id = user_id
            if connected_by_user_id is not None:
                token.connected_by_user_id = connected_by_user_id
            token.updated_at = datetime.now(timezone.utc)

        self.db_session.commit()
        self.db_session.refresh(token)
        return token

    def delete(self) -> None:
        token = self.get()
        if token is None:
            return
        self.db_session.delete(token)
        self.db_session.commit()

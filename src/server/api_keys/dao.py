# -*- coding: utf-8 -*-
"""API Key DAO。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import ApiKey


class ApiKeyDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(
        self,
        *,
        user_id: int,
        name: str,
        key_prefix: str,
        key_hash: str,
        scopes: str,
        expires_at: datetime | None,
    ) -> ApiKey:
        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            expires_at=expires_at,
        )
        self.db_session.add(api_key)
        self.db_session.commit()
        self.db_session.refresh(api_key)
        return api_key

    def get(self, key_id: int) -> ApiKey | None:
        return self.db_session.query(ApiKey).filter(ApiKey.id == key_id).first()

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self.db_session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    def list_for_user(self, user_id: int) -> list[ApiKey]:
        return (
            self.db_session.query(ApiKey)
            .filter(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
            .all()
        )

    def mark_used(self, api_key: ApiKey) -> ApiKey:
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(api_key)
        return api_key

    def revoke(self, api_key: ApiKey) -> ApiKey:
        if api_key.revoked_at is None:
            api_key.revoked_at = datetime.now(timezone.utc)
            api_key.updated_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(api_key)
        return api_key


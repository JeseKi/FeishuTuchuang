# -*- coding: utf-8 -*-
"""OAuth Provider DAO."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import (
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthDeviceCode,
    OAuthProviderRefreshToken,
)


class OAuthClientDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def list_all(self) -> list[OAuthClient]:
        return self.db_session.query(OAuthClient).order_by(OAuthClient.id.desc()).all()

    def get_by_client_id(self, client_id: str) -> OAuthClient | None:
        return (
            self.db_session.query(OAuthClient)
            .filter(OAuthClient.client_id == client_id)
            .first()
        )

    def create(self, client: OAuthClient) -> OAuthClient:
        self.db_session.add(client)
        self.db_session.commit()
        self.db_session.refresh(client)
        return client

    def update(self, client: OAuthClient, **fields) -> OAuthClient:
        for key, value in fields.items():
            setattr(client, key, value)
        client.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(client)
        return client

    def delete(self, client: OAuthClient) -> None:
        self.db_session.delete(client)
        self.db_session.commit()


class OAuthAuthorizationCodeDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, code: OAuthAuthorizationCode) -> OAuthAuthorizationCode:
        self.db_session.add(code)
        self.db_session.commit()
        self.db_session.refresh(code)
        return code

    def get_by_hash(self, code_hash: str) -> OAuthAuthorizationCode | None:
        return (
            self.db_session.query(OAuthAuthorizationCode)
            .filter(OAuthAuthorizationCode.code_hash == code_hash)
            .first()
        )

    def consume(self, code: OAuthAuthorizationCode) -> OAuthAuthorizationCode:
        if code.consumed_at is None:
            code.consumed_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(code)
        return code


class OAuthProviderRefreshTokenDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, refresh_token: OAuthProviderRefreshToken) -> OAuthProviderRefreshToken:
        self.db_session.add(refresh_token)
        self.db_session.commit()
        self.db_session.refresh(refresh_token)
        return refresh_token

    def get_by_hash(self, token_hash: str) -> OAuthProviderRefreshToken | None:
        return (
            self.db_session.query(OAuthProviderRefreshToken)
            .filter(OAuthProviderRefreshToken.token_hash == token_hash)
            .first()
        )

    def revoke(self, refresh_token: OAuthProviderRefreshToken) -> OAuthProviderRefreshToken:
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(refresh_token)
        return refresh_token


class OAuthDeviceCodeDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, device_code: OAuthDeviceCode) -> OAuthDeviceCode:
        self.db_session.add(device_code)
        self.db_session.commit()
        self.db_session.refresh(device_code)
        return device_code

    def get_by_device_code_hash(self, code_hash: str) -> OAuthDeviceCode | None:
        return (
            self.db_session.query(OAuthDeviceCode)
            .filter(OAuthDeviceCode.device_code_hash == code_hash)
            .first()
        )

    def get_by_user_code_hash(self, code_hash: str) -> OAuthDeviceCode | None:
        return (
            self.db_session.query(OAuthDeviceCode)
            .filter(OAuthDeviceCode.user_code_hash == code_hash)
            .first()
        )

    def update(self, device_code: OAuthDeviceCode, **fields) -> OAuthDeviceCode:
        for key, value in fields.items():
            setattr(device_code, key, value)
        self.db_session.commit()
        self.db_session.refresh(device_code)
        return device_code

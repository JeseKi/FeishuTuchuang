# -*- coding: utf-8 -*-
"""Refresh token 持久化与会话管理服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..dao import RefreshTokenDAO, UserDAO
from ..models import RefreshToken, User
from .scopes import get_user_scopes
from .tokens import (
    TOKEN_VERSION_CLAIM,
    create_access_token,
    create_refresh_token_details,
)


def build_token_payload(user: User) -> dict:
    return {
        "sub": user.username,
        "scope": get_user_scopes(user),
        TOKEN_VERSION_CLAIM: user.token_version,
    }


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    token_payload = build_token_payload(user)
    access_token = create_access_token(data=token_payload)
    refresh_token, jti, expires_at = create_refresh_token_details(data=token_payload)
    RefreshTokenDAO(db).create(user_id=user.id, jti=jti, expires_at=expires_at)
    return access_token, refresh_token


def rotate_refresh_token(
    db: Session, user: User, refresh_session: RefreshToken
) -> tuple[str, str]:
    refresh_token_dao = RefreshTokenDAO(db)
    refresh_token_dao.revoke(refresh_session)
    return issue_token_pair(db, user)


def revoke_refresh_token(db: Session, jti: str) -> bool:
    refresh_token = RefreshTokenDAO(db).get_by_jti(jti)
    if refresh_token is None:
        return False
    RefreshTokenDAO(db).revoke(refresh_token)
    return True


def revoke_all_user_sessions(db: Session, user: User) -> User:
    RefreshTokenDAO(db).revoke_all_for_user(user.id)
    return UserDAO(db).bump_token_version(user)


def is_refresh_session_active(refresh_session: RefreshToken) -> bool:
    if refresh_session.revoked_at is not None:
        return False
    expires_at = refresh_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)

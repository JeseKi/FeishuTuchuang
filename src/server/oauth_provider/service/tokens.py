# -*- coding: utf-8 -*-
"""OAuth Provider token service."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.config import auth_config
from src.server.auth.dao import UserDAO
from src.server.auth.models import User

from ..dao import OAuthAuthorizationCodeDAO, OAuthProviderRefreshTokenDAO
from ..models import OAuthProviderRefreshToken
from .authorization import is_code_active
from .constants import ACCESS_TOKEN_TTL_MINUTES, REFRESH_TOKEN_TTL_DAYS
from .crypto import hash_secret, verify_pkce
from .validators import assert_client_secret, get_active_client


def exchange_authorization_code(
    db: Session,
    *,
    client_id: str,
    client_secret: str | None,
    code: str,
    redirect_uri: str,
    code_verifier: str | None,
) -> dict:
    client = get_active_client(db, client_id)
    assert_client_secret(client, client_secret)

    code_record = OAuthAuthorizationCodeDAO(db).get_by_hash(hash_secret(code))
    if code_record is None or not is_code_active(code_record):
        raise invalid_grant()
    if code_record.client_id != client.client_id or code_record.redirect_uri != redirect_uri:
        raise invalid_grant()
    if not code_verifier or not verify_pkce(code_verifier, code_record.code_challenge):
        raise invalid_grant("PKCE 校验失败")

    user = UserDAO(db).get_by_id(code_record.user_id)
    if user is None or auth_service.is_user_disabled(user):
        raise invalid_grant()

    OAuthAuthorizationCodeDAO(db).consume(code_record)
    return issue_external_token_pair(db, client.client_id, user, code_record.scope)


def refresh_external_token(
    db: Session,
    *,
    client_id: str,
    client_secret: str | None,
    refresh_token: str,
) -> dict:
    client = get_active_client(db, client_id)
    assert_client_secret(client, client_secret)

    token_dao = OAuthProviderRefreshTokenDAO(db)
    token_record = token_dao.get_by_hash(hash_secret(refresh_token))
    if token_record is None or not is_refresh_token_active(token_record):
        raise invalid_grant()
    if token_record.client_id != client.client_id:
        raise invalid_grant()

    user = UserDAO(db).get_by_id(token_record.user_id)
    if user is None or auth_service.is_user_disabled(user):
        raise invalid_grant()

    token_dao.revoke(token_record)
    return issue_external_token_pair(db, client.client_id, user, token_record.scope)


def revoke_token(db: Session, token: str, client_id: str, client_secret: str | None) -> None:
    client = get_active_client(db, client_id)
    assert_client_secret(client, client_secret)
    token_record = OAuthProviderRefreshTokenDAO(db).get_by_hash(hash_secret(token))
    if token_record is not None and token_record.client_id == client.client_id:
        OAuthProviderRefreshTokenDAO(db).revoke(token_record)


def issue_external_token_pair(db: Session, client_id: str, user: User, scope: str) -> dict:
    scope_claim = auth_service.serialize_scopes(scope)
    now = datetime.now(timezone.utc)
    access_expire = now + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
    access_payload = {
        "sub": user.username,
        "uid": user.id,
        "client_id": client_id,
        "aud": client_id,
        "scope": scope_claim,
        auth_service.TOKEN_VERSION_CLAIM: user.token_version,
        "exp": access_expire,
        "type": auth_service.TOKEN_TYPE_ACCESS,
        "oauth_provider": True,
    }
    access_token = jwt.encode(
        access_payload, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
    )

    raw_refresh_token = f"opr_{secrets.token_urlsafe(48)}"
    OAuthProviderRefreshTokenDAO(db).create(
        OAuthProviderRefreshToken(
            token_hash=hash_secret(raw_refresh_token),
            client_id=client_id,
            user_id=user.id,
            scope=scope_claim,
            expires_at=now + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        )
    )
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_MINUTES * 60,
        "scope": scope_claim,
    }


def is_refresh_token_active(token: OAuthProviderRefreshToken) -> bool:
    if token.revoked_at is not None:
        return False
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def invalid_grant(detail: str = "invalid_grant") -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

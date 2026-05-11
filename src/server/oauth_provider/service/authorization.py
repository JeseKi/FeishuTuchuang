# -*- coding: utf-8 -*-
"""OAuth Provider authorization service."""

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.models import User

from ..dao import OAuthAuthorizationCodeDAO
from ..models import OAuthAuthorizationCode
from .constants import AUTHORIZATION_CODE_TTL_MINUTES
from .crypto import hash_secret
from .serializers import permission_to_out
from .validators import validate_authorize_request


def get_authorize_metadata(
    db: Session,
    *,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str | None,
    code_challenge: str | None,
    code_challenge_method: str | None,
) -> dict:
    client, scopes = validate_authorize_request(
        db,
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )
    return {
        "client_id": client.client_id,
        "client_name": client.name,
        "redirect_uri": redirect_uri,
        "permissions": [permission_to_out(scope_item) for scope_item in scopes],
        "state": state,
    }


def create_authorization_redirect(db: Session, payload, user: User) -> str:
    client, scopes = validate_authorize_request(
        db,
        response_type=payload.response_type,
        client_id=payload.client_id,
        redirect_uri=payload.redirect_uri,
        scope=payload.scope,
        code_challenge=payload.code_challenge,
        code_challenge_method=payload.code_challenge_method,
    )

    if not payload.approve:
        return build_redirect_url(
            payload.redirect_uri,
            {"error": "access_denied", "state": payload.state},
        )

    user_scopes = set(auth_service.get_user_scopes(user))
    if any(scope not in user_scopes for scope in scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户缺少请求的权限")

    raw_code = f"ocd_{secrets.token_urlsafe(48)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=AUTHORIZATION_CODE_TTL_MINUTES)
    OAuthAuthorizationCodeDAO(db).create(
        OAuthAuthorizationCode(
            code_hash=hash_secret(raw_code),
            client_id=client.client_id,
            user_id=user.id,
            redirect_uri=payload.redirect_uri,
            scope=auth_service.serialize_scopes(scopes),
            code_challenge=payload.code_challenge,
            code_challenge_method="S256",
            expires_at=expires_at,
        )
    )
    return build_redirect_url(payload.redirect_uri, {"code": raw_code, "state": payload.state})


def build_redirect_url(redirect_uri: str, params: dict[str, str | None]) -> str:
    query = urlencode({key: value for key, value in params.items() if value is not None})
    joiner = "&" if "?" in redirect_uri else "?"
    return f"{redirect_uri}{joiner}{query}" if query else redirect_uri


def is_code_active(code: OAuthAuthorizationCode) -> bool:
    if code.consumed_at is not None:
        return False
    expires_at = code.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)

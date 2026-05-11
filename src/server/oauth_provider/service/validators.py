# -*- coding: utf-8 -*-
"""OAuth Provider validation helpers."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service

from ..dao import OAuthClientDAO
from ..models import OAuthClient
from .crypto import verify_secret
from .serializers import load_json_list


def get_active_client(db: Session, client_id: str) -> OAuthClient:
    client = OAuthClientDAO(db).get_by_client_id(client_id)
    if client is None or not client.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_client")
    return client


def assert_client_secret(client: OAuthClient, client_secret: str | None) -> None:
    if not client_secret or not verify_secret(client_secret, client.client_secret_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")


def validate_authorize_request(
    db: Session,
    *,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str | None,
    code_challenge_method: str | None,
) -> tuple[OAuthClient, tuple[str, ...]]:
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 response_type=code"
        )
    client = get_active_client(db, client_id)
    if redirect_uri not in load_json_list(client.redirect_uris):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri 未注册")
    if client.require_pkce:
        if not code_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 code_challenge"
            )
        if code_challenge_method != "S256":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 PKCE S256")

    requested_scopes = auth_service.normalize_scopes(scope)
    allowed_scopes = set(auth_service.normalize_scopes(client.allowed_scopes))
    if any(item not in allowed_scopes for item in requested_scopes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求 scope 超出客户端授权范围")
    return client, requested_scopes

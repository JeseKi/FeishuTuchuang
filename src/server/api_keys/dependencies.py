# -*- coding: utf-8 -*-
"""API Key 认证依赖。"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import SecurityScopes
from sqlalchemy.orm import Session

from src.server.database import get_db

from . import service


async def get_current_api_key_user(
    security_scopes: SecurityScopes,
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    raw_key = _extract_api_key(x_api_key, authorization)
    user, api_key = service.authenticate_api_key(db, raw_key=raw_key)
    service.validate_api_key_scopes(api_key, security_scopes.scopes)
    request.state.user_id = user.id
    request.state.api_key_id = api_key.id
    return user


def _extract_api_key(
    x_api_key: str | None,
    authorization: str | None,
) -> str:
    if isinstance(x_api_key, str) and x_api_key.strip():
        return x_api_key.strip()

    if isinstance(authorization, str):
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials.strip():
            return credentials.strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="缺少 API Key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


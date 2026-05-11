# -*- coding: utf-8 -*-
"""JWT 与安全 token 相关服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional

from jose import jwt

from ..config import auth_config
from .scopes import normalize_scopes, serialize_scopes


TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_VERSION_CLAIM = "tv"


def generate_reset_token() -> str:
    """生成 64 位安全随机 token（hex 格式）。"""
    return secrets.token_hex(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=auth_config.access_token_ttl_minutes)
    )
    scope_claim = serialize_scopes(to_encode.get("scope"))
    if scope_claim:
        to_encode["scope"] = scope_claim
    else:
        to_encode.pop("scope", None)
    to_encode[TOKEN_VERSION_CLAIM] = int(to_encode.get(TOKEN_VERSION_CLAIM, 0))
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_ACCESS})
    return jwt.encode(
        to_encode, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
    )


def create_refresh_token_details(
    data: dict, expires_delta: Optional[timedelta] = None
) -> tuple[str, str, datetime]:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=auth_config.refresh_token_ttl_days)
    )
    scope_claim = serialize_scopes(normalize_scopes(to_encode.get("scope")))
    if scope_claim:
        to_encode["scope"] = scope_claim
    else:
        to_encode.pop("scope", None)
    to_encode[TOKEN_VERSION_CLAIM] = int(to_encode.get(TOKEN_VERSION_CLAIM, 0))
    jti = secrets.token_urlsafe(24)
    to_encode.update({"exp": expire, "type": TOKEN_TYPE_REFRESH, "jti": jti})
    return (
        jwt.encode(
            to_encode, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
        ),
        jti,
        expire,
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    token, _, _ = create_refresh_token_details(data=data, expires_delta=expires_delta)
    return token


def get_token_version(payload: dict) -> int:
    raw_value = payload.get(TOKEN_VERSION_CLAIM, 0)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return -1


def token_version_matches(payload: dict, expected_version: int) -> bool:
    return get_token_version(payload) == expected_version

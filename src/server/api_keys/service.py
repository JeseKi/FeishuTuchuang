# -*- coding: utf-8 -*-
"""API Key 业务服务。"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import secrets
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserStatus
from src.server.auth.service.scopes import (
    SCOPE_IMAGES_WRITE,
    deserialize_scopes,
    get_user_scopes,
    serialize_scopes,
)
from src.server.auth.dependencies.exceptions import insufficient_scopes_exception

from .dao import ApiKeyDAO
from .models import ApiKey
from .schemas import ApiKeyCreate

API_KEY_PREFIX = "ftc_"
DEFAULT_API_KEY_SCOPES = (SCOPE_IMAGES_WRITE,)


def generate_api_key() -> str:
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def create_api_key(
    db: Session,
    *,
    current_user: User,
    payload: ApiKeyCreate,
) -> tuple[ApiKey, str]:
    normalized_scopes = _validate_requested_scopes(current_user, payload.scopes)
    if not normalized_scopes:
        normalized_scopes = DEFAULT_API_KEY_SCOPES

    if payload.expires_at is not None and _as_utc(payload.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="过期时间必须晚于当前时间",
        )

    raw_key = generate_api_key()
    api_key = ApiKeyDAO(db).create(
        user_id=current_user.id,
        name=payload.name,
        key_prefix=raw_key[:12],
        key_hash=hash_api_key(raw_key),
        scopes=serialize_scopes(normalized_scopes),
        expires_at=payload.expires_at,
    )
    return api_key, raw_key


def list_api_keys(db: Session, *, current_user: User) -> list[ApiKey]:
    return ApiKeyDAO(db).list_for_user(current_user.id)


def revoke_api_key(db: Session, *, current_user: User, key_id: int) -> None:
    dao = ApiKeyDAO(db)
    api_key = dao.get(key_id)
    if api_key is None or api_key.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")
    dao.revoke(api_key)


def authenticate_api_key(db: Session, *, raw_key: str) -> tuple[User, ApiKey]:
    api_key = ApiKeyDAO(db).get_by_hash(hash_api_key(raw_key))
    if api_key is None or not is_api_key_active(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 无效或已过期",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    user = db.query(User).filter(User.id == api_key.user_id).first()
    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 用户不可用",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    ApiKeyDAO(db).mark_used(api_key)
    return user, api_key


def validate_api_key_scopes(api_key: ApiKey, required_scopes: Sequence[str]) -> None:
    if not required_scopes:
        return
    granted_scopes = deserialize_scopes(api_key.scopes)
    if any(scope not in granted_scopes for scope in required_scopes):
        raise insufficient_scopes_exception(required_scopes, granted_scopes)


def is_api_key_active(api_key: ApiKey) -> bool:
    if api_key.revoked_at is not None:
        return False
    if api_key.expires_at is None:
        return True
    return _as_utc(api_key.expires_at) > datetime.now(timezone.utc)


def to_output(api_key: ApiKey) -> dict:
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "scopes": list(deserialize_scopes(api_key.scopes)),
        "expires_at": api_key.expires_at,
        "last_used_at": api_key.last_used_at,
        "revoked_at": api_key.revoked_at,
        "created_at": api_key.created_at,
    }


def to_create_output(api_key: ApiKey, raw_key: str) -> dict:
    return {**to_output(api_key), "key": raw_key}


def _validate_requested_scopes(user: User, scopes: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(deserialize_scopes(scopes))
    allowed = set(get_user_scopes(user))
    invalid = [scope for scope in normalized if scope not in allowed]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前用户不能创建这些 scope 的 API Key: {', '.join(invalid)}",
        )
    return normalized


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


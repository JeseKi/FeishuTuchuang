# -*- coding: utf-8 -*-
"""OAuth Provider device authorization service."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.dao import UserDAO
from src.server.auth.models import User
from src.server.config import global_config

from ..dao import OAuthDeviceCodeDAO
from ..models import OAuthClient, OAuthDeviceCode
from .constants import DEVICE_CODE_INTERVAL_SECONDS, DEVICE_CODE_TTL_MINUTES
from .crypto import hash_secret
from .serializers import permission_to_out
from .tokens import invalid_grant, issue_external_token_pair
from .validators import assert_client_secret, get_active_client

DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def create_device_authorization(
    db: Session,
    *,
    client_id: str,
    scope: str,
) -> dict:
    client = get_active_client(db, client_id)
    scopes = validate_device_scopes(client, scope)

    raw_device_code = f"odc_{secrets.token_urlsafe(48)}"
    user_code = _generate_unique_user_code(db)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=DEVICE_CODE_TTL_MINUTES)

    OAuthDeviceCodeDAO(db).create(
        OAuthDeviceCode(
            device_code_hash=hash_secret(raw_device_code),
            user_code_hash=hash_secret(_normalize_user_code(user_code)),
            client_id=client.client_id,
            scope=auth_service.serialize_scopes(scopes),
            expires_at=expires_at,
            interval_seconds=DEVICE_CODE_INTERVAL_SECONDS,
        )
    )

    verification_uri = _build_verification_uri()
    verification_uri_complete = _append_query(verification_uri, {"user_code": user_code})
    return {
        "device_code": raw_device_code,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "verification_uri_complete": verification_uri_complete,
        "expires_in": DEVICE_CODE_TTL_MINUTES * 60,
        "interval": DEVICE_CODE_INTERVAL_SECONDS,
    }


def get_device_authorization_metadata(db: Session, user_code: str) -> dict:
    device_code = _get_active_device_code_by_user_code(db, user_code)
    if device_code.approved_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权已完成")
    if device_code.denied_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权已拒绝")

    client = get_active_client(db, device_code.client_id)
    scopes = auth_service.normalize_scopes(device_code.scope)
    return {
        "client_id": client.client_id,
        "client_name": client.name,
        "user_code": _format_user_code(_normalize_user_code(user_code)),
        "permissions": [permission_to_out(scope_item) for scope_item in scopes],
        "expires_at": device_code.expires_at,
    }


def confirm_device_authorization(
    db: Session,
    *,
    user_code: str,
    approve: bool,
    user: User,
) -> dict:
    device_code = _get_active_device_code_by_user_code(db, user_code)
    if device_code.approved_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权已完成")
    if device_code.denied_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权已拒绝")

    now = datetime.now(timezone.utc)
    dao = OAuthDeviceCodeDAO(db)
    if not approve:
        dao.update(device_code, denied_at=now)
        return {"status": "denied"}

    scopes = auth_service.normalize_scopes(device_code.scope)
    user_scopes = set(auth_service.get_user_scopes(user))
    if any(scope not in user_scopes for scope in scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户缺少请求的权限")

    dao.update(device_code, user_id=user.id, approved_at=now)
    return {"status": "approved"}


def exchange_device_code(
    db: Session,
    *,
    client_id: str,
    client_secret: str | None,
    device_code: str,
) -> dict:
    client = get_active_client(db, client_id)
    assert_client_secret(client, client_secret)

    dao = OAuthDeviceCodeDAO(db)
    code_record = dao.get_by_device_code_hash(hash_secret(device_code))
    if code_record is None or code_record.client_id != client.client_id:
        raise invalid_grant()
    if code_record.consumed_at is not None:
        raise invalid_grant()
    if not is_device_code_unexpired(code_record):
        raise invalid_grant("expired_token")
    if code_record.denied_at is not None:
        raise invalid_grant("access_denied")

    now = datetime.now(timezone.utc)
    if code_record.approved_at is None:
        if _is_polling_too_fast(code_record, now):
            dao.update(
                code_record,
                last_polled_at=now,
                interval_seconds=code_record.interval_seconds + 5,
            )
            raise invalid_grant("slow_down")
        dao.update(code_record, last_polled_at=now)
        raise invalid_grant("authorization_pending")

    if code_record.user_id is None:
        raise invalid_grant()
    user = UserDAO(db).get_by_id(code_record.user_id)
    if user is None or auth_service.is_user_disabled(user):
        raise invalid_grant()

    dao.update(code_record, consumed_at=now)
    return issue_external_token_pair(db, client.client_id, user, code_record.scope)


def validate_device_scopes(client: OAuthClient, scope: str) -> tuple[str, ...]:
    requested_scopes = auth_service.normalize_scopes(scope)
    allowed_scopes = set(auth_service.normalize_scopes(client.allowed_scopes))
    if any(item not in allowed_scopes for item in requested_scopes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求 scope 超出客户端授权范围")
    return requested_scopes


def is_device_code_unexpired(device_code: OAuthDeviceCode) -> bool:
    return _ensure_aware(device_code.expires_at) > datetime.now(timezone.utc)


def _get_active_device_code_by_user_code(db: Session, user_code: str) -> OAuthDeviceCode:
    normalized = _normalize_user_code(user_code)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权码无效或已过期")
    device_code = OAuthDeviceCodeDAO(db).get_by_user_code_hash(hash_secret(normalized))
    if (
        device_code is None
        or device_code.consumed_at is not None
        or not is_device_code_unexpired(device_code)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="授权码无效或已过期")
    return device_code


def _generate_unique_user_code(db: Session) -> str:
    dao = OAuthDeviceCodeDAO(db)
    for _ in range(20):
        normalized = "".join(secrets.choice(USER_CODE_ALPHABET) for _ in range(8))
        if dao.get_by_user_code_hash(hash_secret(normalized)) is None:
            return _format_user_code(normalized)
    normalized = "".join(secrets.choice(USER_CODE_ALPHABET) for _ in range(10))
    return _format_user_code(normalized)


def _normalize_user_code(user_code: str) -> str:
    return "".join(ch for ch in user_code.upper() if ch.isalnum())


def _format_user_code(normalized: str) -> str:
    return "-".join(normalized[index : index + 4] for index in range(0, len(normalized), 4))


def _build_verification_uri() -> str:
    base_url = global_config.app_domain.strip().rstrip("/")
    return f"{base_url}/oauth/device" if base_url else "/oauth/device"


def _append_query(uri: str, params: dict[str, str]) -> str:
    joiner = "&" if "?" in uri else "?"
    return f"{uri}{joiner}{urlencode(params)}"


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _is_polling_too_fast(device_code: OAuthDeviceCode, now: datetime) -> bool:
    if device_code.last_polled_at is None:
        return False
    last_polled_at = _ensure_aware(device_code.last_polled_at)
    return (now - last_polled_at).total_seconds() < device_code.interval_seconds

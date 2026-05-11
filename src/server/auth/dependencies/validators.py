# -*- coding: utf-8 -*-
"""认证依赖校验逻辑。"""

from collections.abc import Sequence

from fastapi import Request
from jose import jwt
from sqlalchemy.orm import Session

from src.server.scope_management.service import has_dangerous_scope

from .. import service
from ..config import auth_config
from ..models import User
from .exceptions import (
    credentials_exception,
    dangerous_scope_requires_two_factor_exception,
    insufficient_scopes_exception,
)
from .security import TWO_FACTOR_CODE_HEADER


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
        options={"verify_aud": False},
    )


def validate_token_type(payload: dict, expected_type: str) -> str:
    username: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")
    if username is None or token_type != expected_type:
        raise credentials_exception()
    return username


def validate_scopes(payload: dict, required_scopes: Sequence[str]) -> None:
    if not required_scopes:
        return

    granted_scopes = service.deserialize_scopes(payload.get("scope"))
    if any(scope not in granted_scopes for scope in required_scopes):
        raise insufficient_scopes_exception(required_scopes, granted_scopes)


def validate_user_scopes(user: User, required_scopes: Sequence[str]) -> None:
    if not required_scopes:
        return

    granted_scopes = set(service.get_user_scopes(user))
    if any(scope not in granted_scopes for scope in required_scopes):
        raise insufficient_scopes_exception(required_scopes, granted_scopes)


def validate_token_version(payload: dict, user: User) -> None:
    if not service.token_version_matches(payload, user.token_version):
        raise credentials_exception()


def validate_dangerous_scope_two_factor(
    request: Request,
    db: Session,
    user: User,
    required_scopes: Sequence[str],
) -> None:
    if not required_scopes or not service.is_two_factor_enabled(user):
        return

    if not has_dangerous_scope(db, tuple(required_scopes)):
        return

    code = request.headers.get(TWO_FACTOR_CODE_HEADER)
    if not isinstance(code, str) or not code.strip():
        raise dangerous_scope_requires_two_factor_exception("危险操作需要二步验证")

    try:
        service.assert_valid_two_factor_code(db, user, code.strip())
    except service.TwoFactorError as exc:
        raise dangerous_scope_requires_two_factor_exception(str(exc))

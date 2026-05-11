# -*- coding: utf-8 -*-
"""认证依赖异常构造。"""

from collections.abc import Sequence

from fastapi import HTTPException, status

from .. import service
from .security import TWO_FACTOR_REQUIRED_RESPONSE_HEADER


def get_www_authenticate_value(required_scopes: Sequence[str] | None = None) -> str:
    if required_scopes:
        return f'Bearer scope="{service.serialize_scopes(required_scopes)}"'
    return "Bearer"


def credentials_exception(
    required_scopes: Sequence[str] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": get_www_authenticate_value(required_scopes)},
    )


def dangerous_scope_requires_two_factor_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
        headers={TWO_FACTOR_REQUIRED_RESPONSE_HEADER: "true"},
    )


def insufficient_scopes_exception(
    required_scopes: Sequence[str],
    granted_scopes: Sequence[str] | set[str],
) -> HTTPException:
    required_set = list(service.normalize_scopes(required_scopes))
    granted_set = set(granted_scopes)
    missing_scopes = [scope for scope in required_set if scope not in granted_set]

    required_text = service.serialize_scopes(required_set)
    missing_text = service.serialize_scopes(missing_scopes)
    display_text = missing_text or required_text

    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": f"缺少所需权限: {display_text}",
            "required_scopes": required_set,
            "missing_scopes": missing_scopes,
        },
        headers={
            "WWW-Authenticate": get_www_authenticate_value(required_set),
            "X-Required-Permissions": required_text,
            "X-Missing-Permissions": missing_text,
        },
    )


def insufficient_role_exception(
    required_scopes: Sequence[str],
    role_name: str,
) -> HTTPException:
    required_text = service.serialize_scopes(required_scopes)
    required_set = list(service.normalize_scopes(required_scopes))
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": f'用户角色 "{role_name}" 无权限，缺少所需权限: {required_text}',
            "required_scopes": required_set,
        },
        headers={"WWW-Authenticate": get_www_authenticate_value(required_scopes)},
    )

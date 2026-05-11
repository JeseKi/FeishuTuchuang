# -*- coding: utf-8 -*-
"""管理员认证依赖。"""

from fastapi import Security

from .. import service
from ..models import User
from ..schemas import UserRole
from .current_user import get_current_user
from .exceptions import insufficient_role_exception


async def get_current_admin(
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_ADMIN_USERS_READ]
    ),
) -> User:
    """
    验证当前用户是否为管理员。

    参数:
        current_user: 已验证的用户对象

    返回:
        User: 管理员用户对象

    异常:
        HTTPException: 当用户非管理员时抛出 403 禁止访问异常
    """
    if current_user.role != UserRole.ADMIN:
        raise insufficient_role_exception(
            [service.SCOPE_ADMIN_USERS_READ], UserRole.ADMIN.value
        )
    return current_user


async def get_current_admin_writer(
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_ADMIN_USERS_WRITE]
    ),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise insufficient_role_exception(
            [service.SCOPE_ADMIN_USERS_WRITE], UserRole.ADMIN.value
        )
    return current_user

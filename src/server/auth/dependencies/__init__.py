# -*- coding: utf-8 -*-
"""
认证依赖模块

文件功能：
    提供认证相关的依赖注入函数，用于验证用户身份和权限
"""

from .admin import get_current_admin, get_current_admin_writer
from .current_user import get_current_user
from .refresh import get_current_refresh_session, get_current_refresh_user
from .security import (
    TWO_FACTOR_CODE_HEADER,
    TWO_FACTOR_REQUIRED_RESPONSE_HEADER,
    oauth2_scheme,
)
from .sessions import CurrentRefreshSession

__all__ = [
    "CurrentRefreshSession",
    "TWO_FACTOR_CODE_HEADER",
    "TWO_FACTOR_REQUIRED_RESPONSE_HEADER",
    "get_current_admin",
    "get_current_admin_writer",
    "get_current_refresh_session",
    "get_current_refresh_user",
    "get_current_user",
    "oauth2_scheme",
]

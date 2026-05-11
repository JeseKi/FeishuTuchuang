# -*- coding: utf-8 -*-
"""认证依赖会话类型。"""

from dataclasses import dataclass

from ..models import RefreshToken, User


@dataclass
class CurrentRefreshSession:
    user: User
    refresh_token: RefreshToken
    payload: dict

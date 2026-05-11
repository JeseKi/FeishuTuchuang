# -*- coding: utf-8 -*-
"""认证依赖安全方案配置。"""

from fastapi.security import OAuth2PasswordBearer

from .. import service

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", scopes=service.OAUTH2_SCOPES
)
TWO_FACTOR_CODE_HEADER = "X-2FA-Code"
TWO_FACTOR_REQUIRED_RESPONSE_HEADER = "X-2FA-Required"

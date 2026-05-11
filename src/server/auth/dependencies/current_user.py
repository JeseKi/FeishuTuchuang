# -*- coding: utf-8 -*-
"""当前用户认证依赖。"""

from fastapi import Depends, Request
from fastapi.security import SecurityScopes
from jose import JWTError
from sqlalchemy.orm import Session

from src.server.config import global_config
from src.server.database import get_db

from .. import service
from ..config import auth_config
from ..models import User
from .exceptions import credentials_exception
from .security import oauth2_scheme
from .validators import (
    decode_token,
    validate_dangerous_scope_two_factor,
    validate_scopes,
    validate_token_type,
    validate_token_version,
    validate_user_scopes,
)


async def get_current_user(
    security_scopes: SecurityScopes,
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    验证当前用户的身份并返回用户对象

    参数:
        token: JWT 访问令牌
        db: 数据库会话

    返回:
        User: 当前用户对象

    异常:
        HTTPException: 当令牌无效或用户不存在时抛出 401 未授权异常
    """
    auth_exception = credentials_exception(security_scopes.scopes)

    # 开发和测试环境下的特殊处理
    if global_config.app_env in ["dev", "test"] and token == auth_config.test_token:
        user = db.query(User).filter(User.id == 1).first()
        if user:
            validate_user_scopes(user, security_scopes.scopes)
            validate_dangerous_scope_two_factor(
                request, db, user, security_scopes.scopes
            )
            return user
        raise auth_exception

    try:
        payload = decode_token(token)
        username = validate_token_type(payload, service.TOKEN_TYPE_ACCESS)
        validate_scopes(payload, security_scopes.scopes)
    except JWTError:
        raise auth_exception

    user = service.get_user_by_username(db, username=username)
    if user is None:
        raise auth_exception
    if service.is_user_disabled(user):
        raise credentials_exception()
    validate_token_version(payload, user)
    validate_dangerous_scope_two_factor(request, db, user, security_scopes.scopes)
    return user

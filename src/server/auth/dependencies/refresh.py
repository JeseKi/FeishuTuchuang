# -*- coding: utf-8 -*-
"""刷新令牌认证依赖。"""

from fastapi import Depends, Request
from jose import JWTError
from sqlalchemy.orm import Session

from src.server.database import get_db

from .. import service
from ..config import auth_config
from ..dao import RefreshTokenDAO
from ..models import User
from .exceptions import credentials_exception
from .sessions import CurrentRefreshSession
from .validators import decode_token, validate_token_type, validate_token_version


async def get_current_refresh_session(
    request: Request, db: Session = Depends(get_db)
) -> CurrentRefreshSession:
    auth_exception = credentials_exception()
    token = request.cookies.get(auth_config.refresh_cookie_name)
    if not token:
        raise auth_exception

    try:
        payload = decode_token(token)
        username = validate_token_type(payload, service.TOKEN_TYPE_REFRESH)
    except JWTError:
        raise auth_exception

    user = service.get_user_by_username(db, username=username)
    if user is None:
        raise auth_exception
    if service.is_user_disabled(user):
        raise auth_exception
    validate_token_version(payload, user)

    refresh_jti = payload.get("jti")
    if not isinstance(refresh_jti, str) or not refresh_jti:
        raise auth_exception

    refresh_session = RefreshTokenDAO(db).get_active_by_jti(refresh_jti)
    if refresh_session is None or refresh_session.user_id != user.id:
        raise auth_exception
    if not service.is_refresh_session_active(refresh_session):
        raise auth_exception

    return CurrentRefreshSession(
        user=user, refresh_token=refresh_session, payload=payload
    )


async def get_current_refresh_user(
    current_session: CurrentRefreshSession = Depends(get_current_refresh_session),
) -> User:
    return current_session.user

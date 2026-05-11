# -*- coding: utf-8 -*-
"""OAuth Provider userinfo service."""

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.config import auth_config


def get_userinfo_from_token(db: Session, token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            auth_config.jwt_secret_key,
            algorithms=[auth_config.jwt_algorithm],
            options={"verify_aud": False},
        )
    except JWTError:
        raise credentials_exception
    if payload.get("type") != auth_service.TOKEN_TYPE_ACCESS or not payload.get("oauth_provider"):
        raise credentials_exception
    if auth_service.SCOPE_PROFILE_READ not in auth_service.deserialize_scopes(
        payload.get("scope")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="缺少所需权限: profile:read")
    username = payload.get("sub")
    if not isinstance(username, str):
        raise credentials_exception
    user = auth_service.get_user_by_username(db, username)
    if user is None or auth_service.is_user_disabled(user):
        raise credentials_exception
    if not auth_service.token_version_matches(payload, user.token_version):
        raise credentials_exception
    return {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.name,
    }

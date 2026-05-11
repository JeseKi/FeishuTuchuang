# -*- coding: utf-8 -*-
"""Password reset routes."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.server.config import global_config
from src.server.database import get_db
from .. import service
from ..models import User
from ..schemas import PasswordResetLinkRequest, PasswordResetWithToken
from .base import router


@router.post(
    "/forgot-password/link",
    summary="发送密码重置链接",
    responses={
        200: {"description": "重置链接发送成功"},
        404: {"description": "邮箱不存在"},
        429: {"description": "发送过于频繁"},
        500: {"description": "重置链接发送失败"},
    },
)
async def send_password_reset_link(
    request: Request,
    payload: PasswordResetLinkRequest, db: Session = Depends(get_db)
):
    await service.verify_turnstile_token(
        request=request,
        token=payload.turnstile_token,
        action="auth_forgot_password_link",
    )
    normalized_email = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if not existing_user:
        return {"message": "重置链接已发送"}

    try:
        if not global_config.app_domain:
            raise RuntimeError("APP_DOMAIN 未配置")
        service.send_password_reset_link(normalized_email, global_config.app_domain)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置链接发送失败",
        )
    return {"message": "重置链接已发送"}


@router.post(
    "/forgot-password/reset",
    summary="重置密码",
    responses={
        200: {"description": "密码重置成功"},
        400: {"description": "重置链接无效或已过期"},
        404: {"description": "邮箱不存在"},
    },
)
async def reset_password(
    payload: PasswordResetWithToken, db: Session = Depends(get_db)
):
    normalized_token = payload.token.strip()
    if len(normalized_token) != 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="重置链接无效或已过期"
        )

    email = service.verify_password_reset_token(normalized_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="重置链接无效或已过期"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="重置链接无效或已过期"
        )

    user.set_password(payload.new_password)
    db.commit()
    return {"message": "密码重置成功"}

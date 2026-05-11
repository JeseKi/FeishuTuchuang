# -*- coding: utf-8 -*-
"""Password change routes."""

from fastapi import Depends, HTTPException, Security, status
from sqlalchemy.orm import Session

from src.server.config import global_config
from src.server.database import get_db
from .. import service
from ..dependencies import get_current_user
from ..models import User
from ..schemas import PasswordChangeConfirm
from .base import router


@router.post(
    "/profile/password-change/link",
    summary="发送密码修改确认链接",
    description="向当前登录用户邮箱发送密码修改确认链接，点击后可在页面中设置新密码",
    responses={
        200: {"description": "确认链接发送成功"},
        401: {"description": "未认证或令牌无效"},
        429: {"description": "发送过于频繁"},
        500: {"description": "确认链接发送失败"},
    },
)
async def send_password_change_link(
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_PASSWORD_WRITE]
    ),
):
    try:
        if not global_config.app_domain:
            raise RuntimeError("APP_DOMAIN 未配置")
        service.send_password_change_link(
            user_id=current_user.id,
            email=current_user.email,
            app_domain=global_config.app_domain,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="确认链接发送失败",
        )

    return {"message": "确认链接已发送"}


@router.post(
    "/profile/password-change/confirm",
    summary="确认修改密码",
    description="使用邮件中的确认 token 设置新密码",
    responses={
        200: {"description": "密码修改成功"},
        400: {"description": "确认链接无效或已过期"},
        404: {"description": "用户不存在"},
    },
)
async def confirm_password_change(
    payload: PasswordChangeConfirm, db: Session = Depends(get_db)
):
    normalized_token = payload.token.strip()
    if len(normalized_token) != 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="确认链接无效或已过期"
        )

    user_id = service.verify_password_change_token(normalized_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="确认链接无效或已过期"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="确认链接无效或已过期"
        )

    user.set_password(payload.new_password)
    db.commit()
    return {"message": "密码修改成功"}

# -*- coding: utf-8 -*-
"""Profile routes."""

from fastapi import Depends, HTTPException, Security, status
from sqlalchemy.orm import Session

from src.server.database import get_db
from .. import service
from ..dependencies import get_current_user
from ..models import User
from ..schemas import (
    EmailChangeCodeRequest,
    EmailChangeConfirm,
    UserProfile,
    UserUpdate,
)
from .base import router


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="获取用户资料",
    description="获取当前登录用户的详细信息",
    response_description="返回当前用户的完整资料信息",
    responses={
        200: {"description": "获取用户资料成功"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def get_profile(
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_READ]
    ),
):
    return current_user


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="更新用户资料",
    description="更新当前登录用户的个人信息，包括用户名、姓名等基础资料",
    response_description="返回更新后的用户资料信息",
    responses={
        200: {"description": "用户资料更新成功"},
        400: {"description": "用户名已被注册"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_WRITE]
    ),
    db: Session = Depends(get_db),
):
    update_payload = user_data.model_dump(exclude_unset=True)
    if "username" in update_payload:
        raw_username = update_payload["username"]
        if raw_username is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空"
            )
        normalized_username = raw_username.strip()
        if not normalized_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空"
            )
        existing_user = (
            db.query(User).filter(User.username == normalized_username).first()
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册"
            )
        update_payload["username"] = normalized_username

    normalized_user_data = UserUpdate(**update_payload)
    updated_user = service.update_user(
        db=db, user=current_user, user_data=normalized_user_data
    )
    return updated_user


@router.post(
    "/profile/email-change/code",
    summary="发送邮箱修改验证码",
    responses={
        200: {"description": "验证码发送成功"},
        400: {"description": "邮箱已被使用或与当前邮箱相同"},
        401: {"description": "未认证或令牌无效"},
        429: {"description": "发送过于频繁"},
        500: {"description": "验证码发送失败"},
    },
)
async def send_email_change_code(
    payload: EmailChangeCodeRequest,
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_EMAIL_WRITE]
    ),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    if normalized_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新邮箱不能与当前邮箱相同"
        )

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
        )

    try:
        service.send_verification_code(normalized_email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="验证码发送失败"
        )

    return {"message": "验证码已发送"}


@router.post(
    "/profile/email-change/confirm",
    response_model=UserProfile,
    summary="确认修改邮箱",
    responses={
        200: {"description": "邮箱修改成功"},
        400: {"description": "验证码无效、邮箱已被使用或与当前邮箱相同"},
        401: {"description": "未认证或令牌无效"},
    },
)
async def confirm_email_change(
    payload: EmailChangeConfirm,
    current_user: User = Security(
        get_current_user, scopes=[service.SCOPE_PROFILE_EMAIL_WRITE]
    ),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    if normalized_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新邮箱不能与当前邮箱相同"
        )

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
        )

    if not service.verify_code(normalized_email, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期"
        )

    db_user = db.query(User).filter(User.id == current_user.id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证或令牌无效"
        )

    db_user.email = normalized_email
    db.commit()
    db.refresh(db_user)
    return db_user

# -*- coding: utf-8 -*-
"""
管理员用户管理路由

公开接口：
- GET /api/admin/users
- PATCH /api/admin/users/{user_id}
- DELETE /api/admin/users/{user_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.server.database import get_db
from src.server.auth.dependencies import get_current_admin, get_current_admin_writer
from src.server.auth.models import User

from .schemas import (
    AdminUserCreate,
    AdminUserOut,
    AdminUserScopesUpdate,
    AdminUserUpdate,
)
from . import service

router = APIRouter(prefix="/api/admin", tags=["管理员"])


@router.get(
    "/users",
    response_model=list[AdminUserOut],
    summary="获取用户列表",
    description="管理员查看系统内的用户列表",
    responses={
        200: {"description": "获取用户列表成功"},
        403: {"description": "无管理员权限"},
    },
)
async def list_users(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return service.list_users(db)


@router.post(
    "/users",
    response_model=AdminUserOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="管理员创建新用户",
    responses={
        201: {"description": "创建成功"},
        400: {"description": "请求参数错误"},
        403: {"description": "无管理员权限"},
        409: {"description": "用户名或邮箱已存在"},
    },
)
async def create_user(
    payload: AdminUserCreate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册"
        )

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
        )

    user = service.create_user(
        db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
        status=payload.status,
    )
    return user


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserOut,
    summary="更新用户信息",
    description="管理员更新用户角色、状态或基础信息",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "请求参数错误"},
        403: {"description": "无管理员权限"},
        404: {"description": "用户不存在"},
    },
)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if "username" in update_data and update_data["username"] is not None:
        normalized_username = update_data["username"].strip()
        if not normalized_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空"
            )
        existing_user = (
            db.query(User).filter(User.username == normalized_username).first()
        )
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册"
            )
        update_data["username"] = normalized_username

    if "email" in update_data and update_data["email"] is not None:
        normalized_email = update_data["email"].strip().lower()
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用"
            )
        update_data["email"] = normalized_email

    if user.id == current_admin.id:
        if "role" in update_data and update_data["role"] != current_admin.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色"
            )
        if "status" in update_data and update_data["status"] != current_admin.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的状态"
            )

    password = update_data.pop("password", None)
    if password:
        user.set_password(password)
        db.commit()
        db.refresh(user)

    if update_data:
        user = service.update_user(db, user, update_data)

    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户",
    description="管理员删除指定用户",
    responses={
        204: {"description": "删除成功"},
        400: {"description": "请求参数错误"},
        403: {"description": "无管理员权限"},
        404: {"description": "用户不存在"},
    },
)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录用户"
        )

    service.delete_user(db, user)


@router.put(
    "/users/{user_id}/scopes",
    response_model=AdminUserOut,
    summary="更新用户权限范围",
    description="管理员更新指定用户的 scope 范围，范围必须属于该用户角色允许的 scope 子集",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "scope 不合法或请求参数错误"},
        403: {"description": "无管理员权限"},
        404: {"description": "用户不存在"},
    },
)
async def update_user_scopes(
    user_id: int,
    payload: AdminUserScopesUpdate,
    current_admin: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的权限范围"
        )

    try:
        return service.update_user_scopes(db, user, payload.scopes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

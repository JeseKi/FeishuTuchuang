# -*- coding: utf-8 -*-
"""
管理员用户管理服务

公开接口：
- list_users
- get_user_by_id
- update_user
- delete_user
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.server.auth.dao import UserDAO
from src.server.auth.models import User
from src.server.auth.schemas import UserRole, UserStatus
from src.server.auth.service import (
    get_role_scopes,
    revoke_all_user_sessions,
    serialize_scopes,
    validate_scope_overrides,
)


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    name: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
) -> User:
    selected_role = role if role else UserRole.USER
    selected_status = status if status else UserStatus.ACTIVE
    tmp_user = User(
        username=username,
        email=email,
        name=name,
        role=selected_role,
        status=selected_status,
    )
    tmp_user.set_password(password)
    user = UserDAO(db).create(
        tmp_user.username,
        tmp_user.email,
        tmp_user.password_hash,
        role=selected_role,
        status=selected_status,
        scope_overrides=serialize_scopes(get_role_scopes(selected_role)),
    )

    # 更新 name, role, status
    if name is not None:
        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        user = UserDAO(db).update(user, **update_fields)

    return user


def list_users(db: Session) -> list[User]:
    return UserDAO(db).list_all()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return UserDAO(db).get_by_id(user_id)


def update_user(db: Session, user: User, update_data: dict) -> User:
    should_revoke_sessions = False
    next_role = update_data.get("role")
    if isinstance(next_role, UserRole):
        update_data["scope_overrides"] = serialize_scopes(get_role_scopes(next_role))
        should_revoke_sessions = True

    if "status" in update_data:
        should_revoke_sessions = True

    updated_user = UserDAO(db).update(user, **update_data)
    if should_revoke_sessions:
        updated_user = revoke_all_user_sessions(db, updated_user)
    return updated_user


def update_user_scopes(db: Session, user: User, scopes: list[str]) -> User:
    normalized_scopes = validate_scope_overrides(user.role, scopes)
    updated_user = UserDAO(db).update(
        user,
        scope_overrides=serialize_scopes(normalized_scopes),
    )
    return revoke_all_user_sessions(db, updated_user)


def delete_user(db: Session, user: User) -> None:
    UserDAO(db).delete(user)

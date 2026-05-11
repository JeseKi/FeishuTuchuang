# -*- coding: utf-8 -*-
"""用户查询与写入相关服务。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..dao import UserDAO
from ..models import User
from ..schemas import UserCreate, UserUpdate, UserStatus


def is_user_disabled(user: User) -> bool:
    return user.status == UserStatus.INACTIVE


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return UserDAO(db).get_by_username(username)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return UserDAO(db).get_by_email(email)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    login_identifier = username.strip()
    user = get_user_by_username(db, login_identifier)
    if not user:
        user = get_user_by_email(db, login_identifier.lower())
    if not user or not user.check_password(password):
        return None
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    # 先构造密码哈希
    tmp_user = User(username=user_data.username, email=user_data.email)
    tmp_user.set_password(user_data.password)
    return UserDAO(db).create(tmp_user.username, tmp_user.email, tmp_user.password_hash)


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    update_data = user_data.model_dump(exclude_unset=True)
    return UserDAO(db).update(user, **update_data)

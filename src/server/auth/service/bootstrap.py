# -*- coding: utf-8 -*-
"""认证模块初始化相关服务。"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from ..config import auth_config
from ..schemas import UserCreate, UserRole
from .users import create_user, get_user_by_username


def bootstrap_default_admin(session: Session) -> None:
    """引导默认管理员（幂等）。用户名取邮箱 @ 前缀。"""
    admin_email = auth_config.init_admin_email
    admin_username = auth_config.init_admin_name
    user = get_user_by_username(session, admin_username)
    password = auth_config.init_admin_password
    if user:
        return
    try:
        admin_user_data = UserCreate(
            username=admin_username, email=admin_email, password=password
        )
        new_user = create_user(session, admin_user_data)
        new_user.role = UserRole.ADMIN
        session.commit()
        logger.info(f"已引导管理员用户：{admin_username}")
    except Exception as e:
        session.rollback()
        logger.warning(f"引导管理员异常（已忽略）：{e}")

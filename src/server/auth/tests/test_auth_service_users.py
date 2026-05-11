# -*- coding: utf-8 -*-
"""认证服务用户相关测试。"""

from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserCreate, UserRole, UserUpdate
from src.server.auth.service import (
    authenticate_user,
    bootstrap_default_admin,
    create_user,
    get_user_by_username,
    update_user,
)


def test_get_user_by_username(test_db_session: Session):
    """测试根据用户名获取用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    # 测试获取存在的用户
    result = get_user_by_username(test_db_session, "testuser")
    assert result is not None
    assert result.username == "testuser"
    assert result.email == "test@example.com"

    # 测试获取不存在的用户
    result = get_user_by_username(test_db_session, "nonexistent")
    assert result is None


def test_authenticate_user(test_db_session: Session):
    """测试用户认证"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    # 测试正确凭据
    result = authenticate_user(test_db_session, "testuser", "password123")
    assert result is not None
    assert result.username == "testuser"

    # 测试错误密码
    result = authenticate_user(test_db_session, "testuser", "wrongpassword")
    assert result is None

    # 测试不存在的用户
    result = authenticate_user(test_db_session, "nonexistent", "password123")
    assert result is None


def test_authenticate_user_with_email(test_db_session: Session):
    """测试用户可通过邮箱认证"""
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    result = authenticate_user(test_db_session, "TEST@EXAMPLE.COM", "password123")
    assert result is not None
    assert result.username == "testuser"


def test_create_user(test_db_session: Session):
    """测试创建用户"""
    user_data = UserCreate(
        username="newuser", email="newuser@example.com", password="password123"
    )

    user = create_user(test_db_session, user_data)

    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.password_hash is not None
    assert len(user.password_hash) > 0


def test_update_user(test_db_session: Session):
    """测试更新用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")  # 设置密码哈希
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # 更新用户信息
    update_data = UserUpdate(username="updated_user", name="Updated Name")
    updated_user = update_user(test_db_session, user, update_data)

    assert updated_user.username == "updated_user"
    assert updated_user.name == "Updated Name"


def test_bootstrap_default_admin(test_db_session: Session):
    """测试引导默认管理员"""
    # 测试创建新的管理员
    bootstrap_default_admin(test_db_session)

    user = get_user_by_username(test_db_session, "admin")
    assert user is not None
    assert user.username == "admin"
    assert user.email == "admin@example.com"
    assert user.role == UserRole.ADMIN
    assert user.check_password("admin123") is True

    # 测试重复调用不会创建重复用户
    bootstrap_default_admin(test_db_session)

    user_count = test_db_session.query(User).filter(User.username == "admin").count()
    assert user_count == 1

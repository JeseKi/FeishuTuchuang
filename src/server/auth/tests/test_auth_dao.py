# -*- coding: utf-8 -*-
"""
认证DAO层测试
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, sessionmaker

from src.server.auth.dao import RefreshTokenDAO, UserDAO
from src.server.auth.models import User


def test_user_dao_get_by_username(test_db_session: Session):
    """测试根据用户名获取用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    dao = UserDAO(test_db_session)

    # 测试获取存在的用户
    result = dao.get_by_username("testuser")
    assert result is not None
    assert result.username == "testuser"
    assert result.email == "test@example.com"

    # 测试获取不存在的用户
    result = dao.get_by_username("nonexistent")
    assert result is None


def test_user_dao_get_by_email(test_db_session: Session):
    """测试根据邮箱获取用户"""
    user = User(username="mailuser", email="mail@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    dao = UserDAO(test_db_session)

    result = dao.get_by_email("mail@example.com")
    assert result is not None
    assert result.username == "mailuser"
    assert result.email == "mail@example.com"

    result = dao.get_by_email("missing@example.com")
    assert result is None


def test_user_dao_create(test_db_session: Session):
    """测试创建用户"""
    dao = UserDAO(test_db_session)

    user = dao.create("newuser", "newuser@example.com", "hashed_password")

    assert user is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.password_hash == "hashed_password"


def test_user_dao_update(test_db_session: Session):
    """测试更新用户"""
    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")  # 设置密码哈希
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    dao = UserDAO(test_db_session)

    # 更新用户信息
    updated_user = dao.update(user, email="updated@example.com", name="Updated Name")

    assert updated_user.email == "updated@example.com"
    assert updated_user.name == "Updated Name"


def test_user_dao_delete(test_db_session: Session):
    """测试删除用户"""
    user = User(username="deleteuser", email="delete@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    dao = UserDAO(test_db_session)
    dao.delete(user)

    assert dao.get_by_id(user.id) is None


def test_refresh_token_dao_create_and_revoke(test_db_session: Session):
    user = User(username="tokenuser", email="tokenuser@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    dao = RefreshTokenDAO(test_db_session)
    refresh_token = dao.create(
        user_id=user.id,
        jti="refresh-jti-1",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    assert refresh_token.user_id == user.id
    assert dao.get_active_by_jti("refresh-jti-1") is not None

    dao.revoke(refresh_token)

    assert dao.get_active_by_jti("refresh-jti-1") is None


def test_user_dao_bump_token_version(test_db_session: Session):
    user = User(username="versionuser", email="versionuser@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    dao = UserDAO(test_db_session)
    updated_user = dao.bump_token_version(user)

    assert updated_user.token_version == 1


def test_user_dao_bump_token_version_accepts_detached_user(test_db_session: Session):
    user = User(username="detacheduser", email="detacheduser@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    AnotherSession = sessionmaker(bind=test_db_session.get_bind())
    another_session = AnotherSession()
    try:
        dao = UserDAO(another_session)
        updated_user = dao.bump_token_version(user)
        assert updated_user.token_version == 1
    finally:
        another_session.close()


def test_user_dao_update_accepts_detached_user(test_db_session: Session):
    user = User(username="detached_update", email="detached_update@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    AnotherSession = sessionmaker(bind=test_db_session.get_bind())
    another_session = AnotherSession()
    try:
        dao = UserDAO(another_session)
        updated_user = dao.update(
            user,
            email="updated-detached@example.com",
            two_factor_enabled=True,
        )
        assert updated_user.email == "updated-detached@example.com"
        assert updated_user.two_factor_enabled is True
    finally:
        another_session.close()

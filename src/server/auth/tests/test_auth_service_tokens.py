# -*- coding: utf-8 -*-
"""认证服务 token 与会话测试。"""

from datetime import timedelta

from jose import jwt
from sqlalchemy.orm import Session

from src.server.auth.config import auth_config
from src.server.auth.dao import RefreshTokenDAO
from src.server.auth.models import User
from src.server.auth.service import (
    SCOPE_PROFILE_READ,
    SCOPE_PROFILE_WRITE,
    create_access_token,
    create_refresh_token,
    deserialize_scopes,
    issue_token_pair,
    revoke_all_user_sessions,
    serialize_scopes,
    token_version_matches,
)


def test_create_access_token():
    """测试创建访问令牌"""
    data = {"sub": "testuser", "scope": [SCOPE_PROFILE_WRITE, SCOPE_PROFILE_READ]}

    # 测试默认过期时间
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    # 测试自定义过期时间
    token = create_access_token(data, timedelta(minutes=30))
    assert isinstance(token, str)
    assert len(token) > 0
    payload = jwt.decode(
        token, auth_config.jwt_secret_key, algorithms=[auth_config.jwt_algorithm]
    )
    assert payload["type"] == "access"
    assert payload["scope"] == serialize_scopes(
        [SCOPE_PROFILE_READ, SCOPE_PROFILE_WRITE]
    )
    assert deserialize_scopes(payload["scope"]) == {
        SCOPE_PROFILE_READ,
        SCOPE_PROFILE_WRITE,
    }


def test_create_refresh_token():
    """测试创建刷新令牌"""
    data = {"sub": "testuser", "tv": 2}

    # 测试默认过期时间
    token = create_refresh_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    # 测试自定义过期时间
    token = create_refresh_token(data, timedelta(days=7))
    assert isinstance(token, str)
    assert len(token) > 0
    payload = jwt.decode(
        token, auth_config.jwt_secret_key, algorithms=[auth_config.jwt_algorithm]
    )
    assert payload["type"] == "refresh"
    assert "jti" in payload
    assert payload["tv"] == 2


def test_issue_token_pair_persists_refresh_session(test_db_session: Session):
    user = User(username="sessionuser", email="session@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    access_token, refresh_token = issue_token_pair(test_db_session, user)

    assert isinstance(access_token, str)
    payload = jwt.decode(
        refresh_token,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )
    refresh_session = RefreshTokenDAO(test_db_session).get_by_jti(payload["jti"])
    assert refresh_session is not None
    assert refresh_session.user_id == user.id
    assert token_version_matches(payload, user.token_version)


def test_revoke_all_user_sessions_bumps_token_version(test_db_session: Session):
    user = User(username="logoutall", email="logoutall@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    _, refresh_token = issue_token_pair(test_db_session, user)
    payload = jwt.decode(
        refresh_token,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )

    revoke_all_user_sessions(test_db_session, user)

    refresh_session = RefreshTokenDAO(test_db_session).get_by_jti(payload["jti"])
    assert refresh_session is not None
    assert refresh_session.revoked_at is not None
    assert user.token_version == 1

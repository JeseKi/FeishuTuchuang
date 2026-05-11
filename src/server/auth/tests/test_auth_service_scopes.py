# -*- coding: utf-8 -*-
"""认证服务权限范围测试。"""

from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserCreate, UserRole
from src.server.auth.service import (
    SCOPE_PROFILE_READ,
    create_user,
    get_role_scopes,
    get_user_scope_overrides,
    get_user_scopes,
    serialize_scopes,
    validate_scope_overrides,
)


def test_get_user_scopes_prefers_user_scope_overrides(test_db_session: Session):
    user = User(
        username="scoped_user",
        email="scoped_user@example.com",
        role=UserRole.ADMIN,
        scope_overrides=serialize_scopes([SCOPE_PROFILE_READ]),
    )
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()

    assert get_user_scope_overrides(user) == (SCOPE_PROFILE_READ,)
    assert get_user_scopes(user) == (SCOPE_PROFILE_READ,)


def test_validate_scope_overrides_rejects_scope_outside_role():
    try:
        validate_scope_overrides(UserRole.USER, ["admin:users:write"])
    except ValueError as exc:
        assert "不允许分配" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid scope assignment")


def test_validate_scope_overrides_preserves_role_scope_order():
    normalized = validate_scope_overrides(
        UserRole.ADMIN, ["admin:users:write", SCOPE_PROFILE_READ]
    )
    assert normalized == (
        SCOPE_PROFILE_READ,
        "admin:users:write",
    )


def test_create_user_defaults_scope_overrides_to_role_scopes(test_db_session: Session):
    user_data = UserCreate(
        username="scoped_new_user",
        email="scoped_new_user@example.com",
        password="password123",
    )

    user = create_user(test_db_session, user_data)

    assert user.scope_overrides is None
    assert get_user_scopes(user) == get_role_scopes(UserRole.USER)

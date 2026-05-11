# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from src.server.auth import service
from src.server.auth.models import User
from src.server.auth.schemas import UserRole, UserStatus


def test_admin_can_update_user_scope_range(test_client, test_db_session: Session):
    admin = User(
        username="permission_admin",
        email="permission_admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    admin.set_password("Password123")
    member = User(
        username="permission_member",
        email="permission_member@example.com",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    member.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.add(member)
    test_db_session.commit()
    test_db_session.refresh(member)

    admin_token = service.create_access_token(
        {"sub": admin.username, "scope": service.get_user_scopes(admin)}
    )
    update_resp = test_client.put(
        f"/api/admin/users/{member.id}/scopes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"scopes": [service.SCOPE_PROFILE_READ]},
    )
    assert update_resp.status_code == 200, update_resp.text
    data = update_resp.json()
    assert data["scope_overrides"] == [service.SCOPE_PROFILE_READ]
    assert data["effective_scopes"] == [service.SCOPE_PROFILE_READ]
    assert service.SCOPE_PROFILE_WRITE not in data["effective_scopes"]

def test_admin_cannot_assign_scope_outside_user_role_range(
    test_client, test_db_session: Session
):
    admin = User(
        username="permission_admin_invalid",
        email="permission_admin_invalid@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    admin.set_password("Password123")
    member = User(
        username="permission_member_invalid",
        email="permission_member_invalid@example.com",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    member.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.add(member)
    test_db_session.commit()
    test_db_session.refresh(member)

    admin_token = service.create_access_token(
        {"sub": admin.username, "scope": service.get_user_scopes(admin)}
    )
    update_resp = test_client.put(
        f"/api/admin/users/{member.id}/scopes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"scopes": [service.SCOPE_ADMIN_USERS_WRITE]},
    )
    assert update_resp.status_code == 400
    assert "不允许分配" in update_resp.json()["detail"]

def test_updating_user_scope_range_revokes_existing_user_tokens(
    test_client, test_db_session: Session
):
    admin = User(
        username="permission_revoke_admin",
        email="permission_revoke_admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    admin.set_password("Password123")
    member = User(
        username="permission_revoke_member",
        email="permission_revoke_member@example.com",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    member.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.add(member)
    test_db_session.commit()
    test_db_session.refresh(member)

    member_token = service.create_access_token(
        {"sub": member.username, "scope": service.get_user_scopes(member), "tv": member.token_version}
    )
    admin_token = service.create_access_token(
        {"sub": admin.username, "scope": service.get_user_scopes(admin), "tv": admin.token_version}
    )

    update_resp = test_client.put(
        f"/api/admin/users/{member.id}/scopes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"scopes": [service.SCOPE_PROFILE_READ]},
    )
    assert update_resp.status_code == 200, update_resp.text

    profile_resp = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert profile_resp.status_code == 401

def test_updating_user_role_resets_scope_range_and_revokes_existing_tokens(
    test_client, test_db_session: Session
):
    admin = User(
        username="role_reset_admin",
        email="role_reset_admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    admin.set_password("Password123")
    member = User(
        username="role_reset_member",
        email="role_reset_member@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        scope_overrides=service.serialize_scopes(
            [service.SCOPE_PROFILE_READ, service.SCOPE_ADMIN_USERS_READ]
        ),
    )
    member.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.add(member)
    test_db_session.commit()
    test_db_session.refresh(member)

    old_token = service.create_access_token(
        {"sub": member.username, "scope": service.get_user_scopes(member), "tv": member.token_version}
    )
    admin_token = service.create_access_token(
        {"sub": admin.username, "scope": service.get_user_scopes(admin), "tv": admin.token_version}
    )

    update_resp = test_client.patch(
        f"/api/admin/users/{member.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "user"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["role"] == "user"
    assert update_resp.json()["effective_scopes"] == list(
        service.get_role_scopes(UserRole.USER)
    )

    old_profile_resp = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert old_profile_resp.status_code == 401

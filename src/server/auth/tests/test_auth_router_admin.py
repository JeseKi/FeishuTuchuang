# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from src.server.auth import service
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.auth.tests._auth_router_helpers import (
    _auth_headers,
    _auth_headers_with_two_factor,
    _enable_two_factor,
    _login_user,
)


def test_admin_routes_enforce_admin_scopes(test_client, test_db_session):
    admin = User(
        username="scope_admin",
        email="scope_admin@example.com",
        role=UserRole.ADMIN,
    )
    admin.set_password("Password123")
    test_db_session.add(admin)

    user = User(
        username="scope_member",
        email="scope_member@example.com",
        role=UserRole.USER,
    )
    user.set_password("Password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(admin)
    test_db_session.refresh(user)

    user_token = service.create_access_token(
        {"sub": user.username, "scope": service.get_user_scopes(user)}
    )
    user_list_resp = test_client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert user_list_resp.status_code == 403
    assert user_list_resp.json()["detail"]["required_scopes"] == [
        service.SCOPE_ADMIN_USERS_READ
    ]
    assert (
        "admin:users:read"
        in user_list_resp.json()["detail"]["message"]
    )

    forged_user_token = service.create_access_token(
        {
            "sub": user.username,
            "scope": [
                service.SCOPE_ADMIN_USERS_READ,
                service.SCOPE_ADMIN_USERS_WRITE,
            ],
        }
    )
    forged_list_resp = test_client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {forged_user_token}"},
    )
    assert forged_list_resp.status_code == 403
    assert forged_list_resp.json()["detail"]["required_scopes"] == [
        service.SCOPE_ADMIN_USERS_READ
    ]
    assert "admin:users:read" in forged_list_resp.json()["detail"]["message"]

    read_only_admin_token = service.create_access_token(
        {"sub": admin.username, "scope": [service.SCOPE_ADMIN_USERS_READ]}
    )
    list_resp = test_client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {read_only_admin_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text

    patch_resp = test_client.patch(
        f"/api/admin/users/{user.id}",
        json={"name": "Updated by scope"},
        headers={"Authorization": f"Bearer {read_only_admin_token}"},
    )
    assert patch_resp.status_code == 403
    assert patch_resp.json()["detail"]["required_scopes"] == [
        service.SCOPE_ADMIN_USERS_WRITE
    ]
    assert "admin:users:write" in patch_resp.json()["detail"]["message"]

    delete_resp = test_client.delete(
        f"/api/admin/users/{user.id}",
        headers={"Authorization": f"Bearer {read_only_admin_token}"},
    )
    assert delete_resp.status_code == 403
    assert delete_resp.json()["detail"]["required_scopes"] == [
        service.SCOPE_ADMIN_USERS_WRITE
    ]
    assert "admin:users:write" in delete_resp.json()["detail"]["message"]

    write_admin_token = service.create_access_token(
        {
            "sub": admin.username,
            "scope": [
                service.SCOPE_ADMIN_USERS_READ,
                service.SCOPE_ADMIN_USERS_WRITE,
            ],
        }
    )
    updated_resp = test_client.patch(
        f"/api/admin/users/{user.id}",
        json={"name": "Updated by scope"},
        headers={"Authorization": f"Bearer {write_admin_token}"},
    )
    assert updated_resp.status_code == 200, updated_resp.text
    assert updated_resp.json()["name"] == "Updated by scope"

    deleted_resp = test_client.delete(
        f"/api/admin/users/{user.id}",
        headers={"Authorization": f"Bearer {write_admin_token}"},
    )
    assert deleted_resp.status_code == 204, deleted_resp.text
    assert test_db_session.query(User).filter(User.id == user.id).first() is None

def test_dangerous_admin_scope_requires_two_factor_when_enabled(
    test_client, test_db_session: Session
):
    admin = User(
        username="danger_admin",
        email="danger_admin@example.com",
        role=UserRole.ADMIN,
    )
    admin.set_password("Password123")
    user = User(
        username="danger_member",
        email="danger_member@example.com",
        role=UserRole.USER,
    )
    user.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.add(user)
    test_db_session.commit()

    login_resp = _login_user(test_client, username="danger_admin")
    secret, _ = _enable_two_factor(
        test_client, access_token=login_resp.json()["access_token"]
    )

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "danger_admin", "password": "Password123"},
    )
    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_resp.json()["challenge_token"],
            "code": service.generate_totp_code(secret),
        },
    )
    access_token = verify_resp.json()["access_token"]

    list_resp = test_client.get(
        "/api/admin/users",
        headers=_auth_headers(access_token),
    )
    assert list_resp.status_code == 200, list_resp.text

    patch_without_2fa = test_client.patch(
        f"/api/admin/users/{user.id}",
        json={"name": "blocked"},
        headers=_auth_headers(access_token),
    )
    assert patch_without_2fa.status_code == 403
    assert patch_without_2fa.json()["detail"] == "危险操作需要二步验证"

    patch_with_2fa = test_client.patch(
        f"/api/admin/users/{user.id}",
        json={"name": "allowed"},
        headers=_auth_headers_with_two_factor(
            access_token, service.generate_totp_code(secret)
        ),
    )
    assert patch_with_2fa.status_code == 200, patch_with_2fa.text
    assert patch_with_2fa.json()["name"] == "allowed"

def test_admin_cannot_delete_self(test_client, test_db_session):
    admin = User(
        username="self_delete_admin",
        email="self_delete_admin@example.com",
        role=UserRole.ADMIN,
    )
    admin.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.commit()
    test_db_session.refresh(admin)

    admin_token = service.create_access_token(
        {
            "sub": admin.username,
            "scope": [
                service.SCOPE_ADMIN_USERS_READ,
                service.SCOPE_ADMIN_USERS_WRITE,
            ],
        }
    )

    resp = test_client.delete(
        f"/api/admin/users/{admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "不能删除当前登录用户"
    assert test_db_session.query(User).filter(User.id == admin.id).first() is not None

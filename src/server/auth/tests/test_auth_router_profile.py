# -*- coding: utf-8 -*-
import os

from src.server.auth import service
from src.server.auth.models import User
from src.server.auth.schemas import UserRole


def test_profile_with_test_token(test_client, init_test_database):
    os.environ.setdefault("APP_ENV", "test")
    # 使用 test_token 直接访问
    resp = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": "Bearer KISPACE_TEST_TOKEN"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"

def test_update_profile_supports_username_change(test_client):
    email = "profile@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "profile_user",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )

    login = test_client.post(
        "/api/auth/login", json={"username": "profile_user", "password": "Password123"}
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = test_client.put(
        "/api/auth/profile",
        json={"username": "updated_profile_user", "name": "新的昵称"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "updated_profile_user"
    assert data["name"] == "新的昵称"

def test_email_change_flow(test_client):
    # 注册
    email = "bob@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "bob",
            "email": email,
            "password": "OldPassword123",
            "code": code,
        },
    )
    # 登录
    login = test_client.post(
        "/api/auth/login", json={"username": "bob", "password": "OldPassword123"}
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    new_email = "bob.new@example.com"
    resp = test_client.post(
        "/api/auth/profile/email-change/code",
        json={"email": new_email},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    change_code = service.verification_codes[new_email]["code"]
    resp = test_client.post(
        "/api/auth/profile/email-change/confirm",
        json={"email": new_email, "code": change_code},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == new_email

    profile = test_client.get("/api/auth/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == new_email

def test_profile_requires_profile_read_scope(test_client, test_db_session):
    user = User(
        username="scoped_user",
        email="scoped@example.com",
        role=UserRole.USER,
    )
    user.set_password("Password123")
    test_db_session.add(user)
    test_db_session.commit()

    valid_token = service.create_access_token(
        {
            "sub": user.username,
            "scope": [service.SCOPE_PROFILE_READ],
        }
    )
    resp = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == user.username

    missing_scope_token = service.create_access_token({"sub": user.username})
    forbidden = test_client.get(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {missing_scope_token}"},
    )
    assert forbidden.status_code == 403
    forbidden_detail = forbidden.json()["detail"]
    assert forbidden_detail["message"] == "缺少所需权限: profile:read"
    assert forbidden_detail["required_scopes"] == [service.SCOPE_PROFILE_READ]
    assert forbidden.headers.get("X-Missing-Permissions") == "profile:read"

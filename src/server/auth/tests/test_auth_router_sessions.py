# -*- coding: utf-8 -*-
from jose import jwt
from sqlalchemy.orm import Session

from src.server.auth import service
from src.server.auth.config import auth_config
from src.server.auth.dao import RefreshTokenDAO
from src.server.auth.models import User
from src.server.auth.schemas import UserRole


def test_refresh_requires_refresh_cookie(test_client):
    email = "carol@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]

    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "carol",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

    login_resp = test_client.post(
        "/api/auth/login", json={"username": "carol", "password": "Password123"}
    )
    assert login_resp.status_code == 200, login_resp.text
    assert "fullstack_template_refresh_token" in login_resp.cookies
    assert "refresh_token" not in login_resp.json()

    access_token = login_resp.json()["access_token"]
    refresh_cookie = login_resp.cookies.get("fullstack_template_refresh_token")
    assert refresh_cookie is not None

    test_client.cookies.delete("fullstack_template_refresh_token")

    unauthorized = test_client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert unauthorized.status_code == 401

    test_client.cookies.set("fullstack_template_refresh_token", refresh_cookie)

    refreshed = test_client.post("/api/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text
    data = refreshed.json()
    assert "access_token" in data
    assert "refresh_token" not in data
    assert service.deserialize_scopes(data["scope"]) == set(
        service.get_role_scopes(UserRole.USER)
    )

def test_logout_revokes_current_refresh_session(test_client, test_db_session: Session):
    email = "logout@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]

    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "logout_user",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

    login_resp = test_client.post(
        "/api/auth/login", json={"username": "logout_user", "password": "Password123"}
    )
    refresh_cookie = login_resp.cookies.get("fullstack_template_refresh_token")
    assert refresh_cookie is not None
    payload = jwt.decode(
        refresh_cookie,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )

    logout_resp = test_client.post("/api/auth/logout")
    assert logout_resp.status_code == 200, logout_resp.text
    assert logout_resp.json()["message"] == "已退出当前设备"
    refresh_session = RefreshTokenDAO(test_db_session).get_by_jti(payload["jti"])
    assert refresh_session is not None
    assert refresh_session.revoked_at is not None

    refreshed = test_client.post("/api/auth/refresh")
    assert refreshed.status_code == 401

def test_logout_all_revokes_all_devices_immediately(
    test_client, test_db_session: Session
):
    email = "logout-all@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]

    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "logout_all_user",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

    login_resp = test_client.post(
        "/api/auth/login",
        json={"username": "logout_all_user", "password": "Password123"},
    )
    assert login_resp.status_code == 200, login_resp.text

    access_token = login_resp.json()["access_token"]
    refresh_cookie = login_resp.cookies.get("fullstack_template_refresh_token")
    assert refresh_cookie is not None
    payload = jwt.decode(
        refresh_cookie,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )
    old_jti = payload["jti"]

    headers = {"Authorization": f"Bearer {access_token}"}
    logout_all_resp = test_client.post("/api/auth/logout-all", headers=headers)
    assert logout_all_resp.status_code == 200, logout_all_resp.text
    assert logout_all_resp.json()["message"] == "已退出所有设备"

    user = (
        test_db_session.query(User).filter(User.username == "logout_all_user").first()
    )
    assert user is not None
    assert user.token_version == 1

    refresh_session = RefreshTokenDAO(test_db_session).get_by_jti(old_jti)
    assert refresh_session is not None
    assert refresh_session.revoked_at is not None

    expired_access = test_client.get("/api/auth/profile", headers=headers)
    assert expired_access.status_code == 401

    refreshed = test_client.post("/api/auth/refresh")
    assert refreshed.status_code == 401

def test_logout_all_revokes_admin_access_on_other_device(
    test_client, test_db_session: Session
):
    admin = User(
        username="multi_device_admin",
        email="multi_device_admin@example.com",
        role=UserRole.ADMIN,
    )
    admin.set_password("Password123")
    test_db_session.add(admin)
    test_db_session.commit()
    test_db_session.refresh(admin)

    device_a_login = test_client.post(
        "/api/auth/login",
        json={"username": "multi_device_admin", "password": "Password123"},
    )
    assert device_a_login.status_code == 200, device_a_login.text
    device_a_access_token = device_a_login.json()["access_token"]

    device_b_login = test_client.post(
        "/api/auth/login",
        json={"username": "multi_device_admin", "password": "Password123"},
    )
    assert device_b_login.status_code == 200, device_b_login.text
    device_b_access_token = device_b_login.json()["access_token"]
    device_b_refresh_cookie = device_b_login.cookies.get(
        "fullstack_template_refresh_token"
    )
    assert device_b_refresh_cookie is not None

    logout_all_resp = test_client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {device_a_access_token}"},
    )
    assert logout_all_resp.status_code == 200, logout_all_resp.text

    stale_admin_headers = {"Authorization": f"Bearer {device_b_access_token}"}
    list_resp = test_client.get("/api/admin/users", headers=stale_admin_headers)
    assert list_resp.status_code == 401, list_resp.text

    update_resp = test_client.patch(
        f"/api/admin/users/{admin.id}",
        json={"name": "should fail"},
        headers=stale_admin_headers,
    )
    assert update_resp.status_code == 401, update_resp.text

    test_client.cookies.set(
        "fullstack_template_refresh_token",
        device_b_refresh_cookie,
    )
    refresh_resp = test_client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401, refresh_resp.text

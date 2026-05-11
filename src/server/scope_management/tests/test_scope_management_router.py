# -*- coding: utf-8 -*-
from http import HTTPStatus

from src.server.auth import service as auth_service
from src.server.auth.models import User
from src.server.auth.schemas import UserRole, UserStatus


def _login_admin(test_client):
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    access_token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _auth_headers_for_user(user: User) -> dict[str, str]:
    access_token = auth_service.create_access_token(
        {"sub": user.username, "scope": auth_service.get_user_scopes(user)}
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_list_scopes_requires_admin(test_client, test_db_session):
    member = User(
        username="member",
        email="member@example.com",
        password_hash="hashed",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    test_db_session.add(member)
    test_db_session.commit()
    test_db_session.refresh(member)

    resp = test_client.get("/api/admin/scopes", headers=_auth_headers_for_user(member))
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_and_update_scopes(test_client, init_test_database):
    headers = _login_admin(test_client)

    list_resp = test_client.get("/api/admin/scopes", headers=headers)
    assert list_resp.status_code == HTTPStatus.OK, list_resp.text
    scopes = list_resp.json()
    assert any(item["scope"] == "profile:read" for item in scopes)
    profile_read = next(item for item in scopes if item["scope"] == "profile:read")
    assert profile_read["title"] == "查看基础资料"
    assert profile_read["description"] == "读取当前用户的用户名、邮箱、显示名称和账号基础状态。"

    update_resp = test_client.patch(
        "/api/admin/scopes/profile:read",
        headers=headers,
        json={"category": "dangerous"},
    )
    assert update_resp.status_code == HTTPStatus.OK, update_resp.text
    assert update_resp.json()["scope"] == "profile:read"
    assert update_resp.json()["category"] == "dangerous"


def test_list_scopes_requires_authentication(test_client):
    resp = test_client.get("/api/admin/scopes")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

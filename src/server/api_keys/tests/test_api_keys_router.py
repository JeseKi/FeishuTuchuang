# -*- coding: utf-8 -*-
"""API Key 路由测试。"""

from __future__ import annotations

from http import HTTPStatus

from src.server.api_keys.models import ApiKey


def _login_admin(test_client):
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_and_list_api_key(test_client, init_test_database, test_db_session):
    headers = _login_admin(test_client)

    create_resp = test_client.post(
        "/api/auth/api-keys",
        headers=headers,
        json={"name": "PicGo", "scopes": ["images:write"]},
    )

    assert create_resp.status_code == HTTPStatus.CREATED, create_resp.text
    created = create_resp.json()
    assert created["name"] == "PicGo"
    assert created["key"].startswith("ftc_")
    assert created["key_prefix"] == created["key"][:12]
    assert created["scopes"] == ["images:write"]

    stored = test_db_session.query(ApiKey).filter(ApiKey.id == created["id"]).one()
    assert stored.key_hash != created["key"]

    list_resp = test_client.get("/api/auth/api-keys", headers=headers)

    assert list_resp.status_code == HTTPStatus.OK, list_resp.text
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert "key" not in listed[0]


def test_revoke_api_key(test_client, init_test_database):
    headers = _login_admin(test_client)
    create_resp = test_client.post(
        "/api/auth/api-keys",
        headers=headers,
        json={"name": "remote upload"},
    )
    key_id = create_resp.json()["id"]

    revoke_resp = test_client.delete(f"/api/auth/api-keys/{key_id}", headers=headers)
    list_resp = test_client.get("/api/auth/api-keys", headers=headers)

    assert revoke_resp.status_code == HTTPStatus.NO_CONTENT, revoke_resp.text
    assert list_resp.json()[0]["revoked_at"] is not None


def test_create_api_key_rejects_unavailable_scope(test_client, init_test_database):
    headers = _login_admin(test_client)

    resp = test_client.post(
        "/api/auth/api-keys",
        headers=headers,
        json={"name": "bad key", "scopes": ["root:write"]},
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST

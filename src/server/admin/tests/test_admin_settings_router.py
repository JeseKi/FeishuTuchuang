# -*- coding: utf-8 -*-
"""管理员配置路由测试。"""

from __future__ import annotations

from http import HTTPStatus


def _login_admin(test_client):
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    access_token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_admin_settings_default_and_update(test_client, init_test_database):
    headers = _login_admin(test_client)

    get_resp = test_client.get("/api/admin/settings", headers=headers)

    assert get_resp.status_code == HTTPStatus.OK, get_resp.text
    assert get_resp.json() == {"image_cors_allowed_origin": "*"}

    update_resp = test_client.patch(
        "/api/admin/settings",
        headers=headers,
        json={"image_cors_allowed_origin": "https://43.139.69.53:20194"},
    )

    assert update_resp.status_code == HTTPStatus.OK, update_resp.text
    assert update_resp.json() == {
        "image_cors_allowed_origin": "https://43.139.69.53:20194"
    }

    get_updated_resp = test_client.get("/api/admin/settings", headers=headers)
    assert get_updated_resp.status_code == HTTPStatus.OK, get_updated_resp.text
    assert get_updated_resp.json() == update_resp.json()


def test_admin_settings_rejects_empty_origin(test_client, init_test_database):
    headers = _login_admin(test_client)

    resp = test_client.patch(
        "/api/admin/settings",
        headers=headers,
        json={"image_cors_allowed_origin": "   "},
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

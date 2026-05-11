# -*- coding: utf-8 -*-

from __future__ import annotations

from .helpers import ADMIN_HEADERS, create_client


def test_admin_can_create_update_and_reset_oauth_client(test_client, init_test_database):
    created = create_client(test_client)
    assert created["name"] == "Demo OAuth App"
    assert created["allowed_scopes"] == ["profile:read"]

    list_resp = test_client.get("/api/oauth-provider/clients", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert list_resp.json()[0]["client_id"] == created["client_id"]
    assert "client_secret" not in list_resp.json()[0]

    update_resp = test_client.patch(
        f"/api/oauth-provider/clients/{created['client_id']}",
        headers=ADMIN_HEADERS,
        json={"name": "Renamed App", "is_active": False},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["name"] == "Renamed App"
    assert update_resp.json()["is_active"] is False

    reset_resp = test_client.post(
        f"/api/oauth-provider/clients/{created['client_id']}/secret",
        headers=ADMIN_HEADERS,
    )
    assert reset_resp.status_code == 200, reset_resp.text
    assert reset_resp.json()["client_secret"] != created["client_secret"]

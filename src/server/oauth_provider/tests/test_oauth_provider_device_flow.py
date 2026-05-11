# -*- coding: utf-8 -*-

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from .helpers import (
    ADMIN_HEADERS,
    create_client,
    exchange_device_code,
    start_device_authorization,
)


def test_device_code_flow_issues_tokens_after_user_approval(
    test_client, init_test_database
):
    client = create_client(test_client)
    device_resp = start_device_authorization(test_client, client_id=client["client_id"])
    assert device_resp.status_code == 200, device_resp.text
    device_data = device_resp.json()
    assert device_data["device_code"].startswith("odc_")
    assert len(device_data["user_code"].replace("-", "")) == 8
    assert urlparse(device_data["verification_uri"]).path == "/oauth/device"
    complete_url = urlparse(device_data["verification_uri_complete"])
    assert complete_url.path == "/oauth/device"
    assert parse_qs(complete_url.query)["user_code"] == [device_data["user_code"]]
    assert device_data["expires_in"] == 900
    assert device_data["interval"] == 5

    pending_resp = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_data["device_code"],
    )
    assert pending_resp.status_code == 400
    assert pending_resp.json()["detail"] == "authorization_pending"

    metadata_resp = test_client.get(
        "/api/oauth-provider/device/metadata",
        headers=ADMIN_HEADERS,
        params={"user_code": device_data["user_code"].replace("-", " ")},
    )
    assert metadata_resp.status_code == 200, metadata_resp.text
    assert metadata_resp.json()["client_name"] == "Demo OAuth App"
    assert metadata_resp.json()["permissions"][0]["scope"] == "profile:read"

    approve_resp = test_client.post(
        "/api/oauth-provider/device/authorize",
        headers=ADMIN_HEADERS,
        json={"user_code": device_data["user_code"], "approve": True},
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"

    token_resp = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_data["device_code"],
    )
    assert token_resp.status_code == 200, token_resp.text
    token_data = token_resp.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["scope"] == "profile:read"
    assert token_data["access_token"]
    assert token_data["refresh_token"]

    replay_resp = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_data["device_code"],
    )
    assert replay_resp.status_code == 400


def test_device_code_flow_can_be_denied(test_client, init_test_database):
    client = create_client(test_client)
    device_resp = start_device_authorization(test_client, client_id=client["client_id"])
    assert device_resp.status_code == 200, device_resp.text
    device_data = device_resp.json()

    deny_resp = test_client.post(
        "/api/oauth-provider/device/authorize",
        headers=ADMIN_HEADERS,
        json={"user_code": device_data["user_code"], "approve": False},
    )
    assert deny_resp.status_code == 200, deny_resp.text
    assert deny_resp.json()["status"] == "denied"

    token_resp = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_data["device_code"],
    )
    assert token_resp.status_code == 400
    assert token_resp.json()["detail"] == "access_denied"


def test_device_code_flow_returns_slow_down_for_fast_polling(
    test_client, init_test_database
):
    client = create_client(test_client)
    device_resp = start_device_authorization(test_client, client_id=client["client_id"])
    assert device_resp.status_code == 200, device_resp.text
    device_code = device_resp.json()["device_code"]

    first_poll = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_code,
    )
    assert first_poll.status_code == 400
    assert first_poll.json()["detail"] == "authorization_pending"

    second_poll = exchange_device_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        device_code=device_code,
    )
    assert second_poll.status_code == 400
    assert second_poll.json()["detail"] == "slow_down"

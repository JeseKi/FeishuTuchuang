# -*- coding: utf-8 -*-

from __future__ import annotations

from .helpers import (
    ADMIN_HEADERS,
    authorize,
    basic_auth,
    create_client,
    exchange_code,
    pkce_pair,
)


def test_authorization_code_pkce_flow_issues_tokens_and_userinfo(
    test_client, init_test_database
):
    client = create_client(test_client)
    verifier, challenge = pkce_pair()

    metadata_resp = test_client.get(
        "/api/oauth-provider/authorize/metadata",
        headers=ADMIN_HEADERS,
        params={
            "response_type": "code",
            "client_id": client["client_id"],
            "redirect_uri": "https://client.example.com/callback",
            "scope": "profile:read",
            "state": "state-123",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )
    assert metadata_resp.status_code == 200, metadata_resp.text
    assert metadata_resp.json()["client_name"] == "Demo OAuth App"
    assert metadata_resp.json()["permissions"] == [
        {
            "scope": "profile:read",
            "title": "查看基础资料",
            "description": "读取当前用户的用户名、邮箱、显示名称和账号基础状态。",
        }
    ]

    code = authorize(test_client, client["client_id"], challenge)
    token_resp = exchange_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        code=code,
        verifier=verifier,
    )
    assert token_resp.status_code == 200, token_resp.text
    token_data = token_resp.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["scope"] == "profile:read"
    assert token_data["access_token"]
    assert token_data["refresh_token"]

    replay_resp = exchange_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        code=code,
        verifier=verifier,
    )
    assert replay_resp.status_code == 400

    userinfo_resp = test_client.get(
        "/api/oauth-provider/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert userinfo_resp.status_code == 200, userinfo_resp.text
    assert userinfo_resp.json()["username"] == "admin"

    existing_api_resp = test_client.post(
        "/api/example/items",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        json={"name": "from-oauth-provider"},
    )
    assert existing_api_resp.status_code == 201, existing_api_resp.text


def test_token_endpoint_rejects_wrong_pkce_verifier(test_client, init_test_database):
    client = create_client(test_client)
    _, challenge = pkce_pair()
    code = authorize(test_client, client["client_id"], challenge)

    token_resp = exchange_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        code=code,
        verifier="wrong-verifier",
    )
    assert token_resp.status_code == 400


def test_refresh_token_rotates_and_old_token_is_invalid(test_client, init_test_database):
    client = create_client(test_client)
    verifier, challenge = pkce_pair()
    code = authorize(test_client, client["client_id"], challenge)
    token_resp = exchange_code(
        test_client,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        code=code,
        verifier=verifier,
    )
    assert token_resp.status_code == 200, token_resp.text
    first_refresh_token = token_resp.json()["refresh_token"]

    refresh_resp = test_client.post(
        "/api/oauth-provider/token",
        headers={"Authorization": basic_auth(client["client_id"], client["client_secret"])},
        data={
            "grant_type": "refresh_token",
            "refresh_token": first_refresh_token,
        },
    )
    assert refresh_resp.status_code == 200, refresh_resp.text
    second_refresh_token = refresh_resp.json()["refresh_token"]
    assert second_refresh_token != first_refresh_token

    replay_resp = test_client.post(
        "/api/oauth-provider/token",
        headers={"Authorization": basic_auth(client["client_id"], client["client_secret"])},
        data={
            "grant_type": "refresh_token",
            "refresh_token": first_refresh_token,
        },
    )
    assert replay_resp.status_code == 400

    revoke_resp = test_client.post(
        "/api/oauth-provider/revoke",
        headers={"Authorization": basic_auth(client["client_id"], client["client_secret"])},
        data={"token": second_refresh_token},
    )
    assert revoke_resp.status_code == 204

    revoked_resp = test_client.post(
        "/api/oauth-provider/token",
        headers={"Authorization": basic_auth(client["client_id"], client["client_secret"])},
        data={
            "grant_type": "refresh_token",
            "refresh_token": second_refresh_token,
        },
    )
    assert revoked_resp.status_code == 400

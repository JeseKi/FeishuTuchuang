# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import hashlib
from urllib.parse import parse_qs, urlparse


ADMIN_HEADERS = {"Authorization": "Bearer KISPACE_TEST_TOKEN"}


def pkce_pair() -> tuple[str, str]:
    verifier = "test-code-verifier-1234567890"
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def basic_auth(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def create_client(test_client) -> dict:
    resp = test_client.post(
        "/api/oauth-provider/clients",
        headers=ADMIN_HEADERS,
        json={
            "name": "Demo OAuth App",
            "redirect_uris": ["https://client.example.com/callback"],
            "allowed_scopes": ["profile:read"],
            "is_active": True,
            "require_pkce": True,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["client_id"]
    assert data["client_secret"]
    return data


def authorize(test_client, client_id: str, challenge: str) -> str:
    payload = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": "https://client.example.com/callback",
        "scope": "profile:read",
        "state": "state-123",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "approve": True,
    }
    resp = test_client.post(
        "/api/oauth-provider/authorize",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    redirect_url = resp.json()["redirect_url"]
    parsed = urlparse(redirect_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "client.example.com"
    query = parse_qs(parsed.query)
    assert query["state"] == ["state-123"]
    return query["code"][0]


def exchange_code(
    test_client,
    *,
    client_id: str,
    client_secret: str,
    code: str,
    verifier: str,
):
    return test_client.post(
        "/api/oauth-provider/token",
        headers={"Authorization": basic_auth(client_id, client_secret)},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://client.example.com/callback",
            "code_verifier": verifier,
        },
    )


def start_device_authorization(test_client, *, client_id: str, scope: str = "profile:read"):
    return test_client.post(
        "/api/oauth-provider/device_authorization",
        data={
            "client_id": client_id,
            "scope": scope,
        },
    )


def exchange_device_code(
    test_client,
    *,
    client_id: str,
    client_secret: str,
    device_code: str,
):
    return test_client.post(
        "/api/oauth-provider/token",
        headers={"Authorization": basic_auth(client_id, client_secret)},
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
        },
    )

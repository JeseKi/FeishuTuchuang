# -*- coding: utf-8 -*-
from src.server.auth import service
from src.server.auth.tests._auth_router_helpers import (
    _auth_headers,
    _auth_headers_with_two_factor,
    _enable_two_factor,
    _login_user,
)
from src.server.config import global_config


def test_password_change_flow(test_client, monkeypatch):
    monkeypatch.setattr(global_config, "app_domain", "http://localhost:5173")

    email = "password-change@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "pwd_user",
            "email": email,
            "password": "OldPassword123",
            "code": code,
        },
    )

    resp = test_client.post(
        "/api/auth/login", json={"username": "pwd_user", "password": "OldPassword123"}
    )
    assert resp.status_code == 200, resp.text
    access_token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = test_client.post("/api/auth/profile/password-change/link", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "确认链接已发送"

    token = next(iter(service.password_change_tokens))
    resp = test_client.post(
        "/api/auth/profile/password-change/confirm",
        json={"token": token, "new_password": "NewPassword123"},
    )
    assert resp.status_code == 200, resp.text

    resp = test_client.post(
        "/api/auth/login", json={"username": "pwd_user", "password": "NewPassword123"}
    )
    assert resp.status_code == 200

def test_password_change_link_requires_two_factor_for_two_factor_users(
    test_client, monkeypatch
):
    monkeypatch.setattr(global_config, "app_domain", "http://localhost:5173")
    service.password_change_tokens.clear()
    service.password_change_request_log.clear()

    email = "password-change-2fa@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "pwd_2fa_user",
            "email": email,
            "password": "OldPassword123",
            "code": code,
        },
    )

    first_login = _login_user(
        test_client, username="pwd_2fa_user", password="OldPassword123"
    )
    secret, _ = _enable_two_factor(
        test_client, access_token=first_login.json()["access_token"]
    )

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "pwd_2fa_user", "password": "OldPassword123"},
    )
    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_resp.json()["challenge_token"],
            "code": service.generate_totp_code(secret),
        },
    )
    access_token = verify_resp.json()["access_token"]

    missing_code_resp = test_client.post(
        "/api/auth/profile/password-change/link",
        headers=_auth_headers(access_token),
    )
    assert missing_code_resp.status_code == 403
    assert missing_code_resp.json()["detail"] == "危险操作需要二步验证"

    invalid_code_resp = test_client.post(
        "/api/auth/profile/password-change/link",
        headers=_auth_headers_with_two_factor(access_token, "000000"),
    )
    assert invalid_code_resp.status_code == 403
    assert "错误" in invalid_code_resp.json()["detail"]

    valid_code_resp = test_client.post(
        "/api/auth/profile/password-change/link",
        headers=_auth_headers_with_two_factor(
            access_token, service.generate_totp_code(secret)
        ),
    )
    assert valid_code_resp.status_code == 200
    assert valid_code_resp.json()["message"] == "确认链接已发送"

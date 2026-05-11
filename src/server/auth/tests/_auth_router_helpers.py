# -*- coding: utf-8 -*-
from src.server.auth import service


def _register_user(
    test_client, *, username: str, email: str, password: str = "Password123"
):
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": username,
            "email": email,
            "password": password,
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

def _login_user(test_client, *, username: str, password: str = "Password123"):
    resp = test_client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp

def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}

def _auth_headers_with_two_factor(access_token: str, code: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-2FA-Code": code,
    }

def _enable_two_factor(
    test_client,
    *,
    access_token: str,
) -> tuple[str, list[str]]:
    headers = _auth_headers(access_token)
    start_resp = test_client.post("/api/auth/2fa/setup/start", headers=headers)
    assert start_resp.status_code == 200, start_resp.text
    start_data = start_resp.json()
    confirm_resp = test_client.post(
        "/api/auth/2fa/setup/confirm",
        headers=headers,
        json={
            "setup_token": start_data["setup_token"],
            "code": service.generate_totp_code(start_data["secret"]),
        },
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    return start_data["secret"], confirm_resp.json()["backup_codes"]

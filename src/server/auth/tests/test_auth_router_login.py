# -*- coding: utf-8 -*-
from jose import jwt
from sqlalchemy.orm import Session

from src.server.auth import service
from src.server.auth.config import auth_config
from src.server.auth.dao import RefreshTokenDAO
from src.server.auth.schemas import UserRole


def test_register_and_login_flow(test_client, test_db_session: Session):
    email = "alice@example.com"
    # 注册
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]

    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "alice",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

    # 登录
    resp = test_client.post(
        "/api/auth/login", json={"username": "alice", "password": "Password123"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" not in data
    assert service.deserialize_scopes(data["scope"]) == set(
        service.get_role_scopes(UserRole.USER)
    )
    refresh_cookie = resp.cookies.get("fullstack_template_refresh_token")
    assert refresh_cookie is not None
    payload = jwt.decode(
        refresh_cookie,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )
    assert RefreshTokenDAO(test_db_session).get_by_jti(payload["jti"]) is not None

def test_login_wrong_password(test_client, init_test_database):
    resp = test_client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert resp.status_code == 401

def test_login_with_email(test_client):
    email = "login-by-email@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]

    resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "email_login_user",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )
    assert resp.status_code == 201, resp.text

    resp = test_client.post(
        "/api/auth/login", json={"username": email.upper(), "password": "Password123"}
    )
    assert resp.status_code == 200, resp.text
    assert "access_token" in resp.json()

def test_send_verification_code_hides_existing_email(test_client):
    email = "dave@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text
    code = service.verification_codes[email]["code"]
    test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "dave",
            "email": email,
            "password": "Password123",
            "code": code,
        },
    )

    repeat = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert repeat.status_code == 200
    assert repeat.json()["message"] == "验证码已发送"

def test_password_reset_hides_unknown_email(test_client):
    resp = test_client.post(
        "/api/auth/forgot-password/link", json={"email": "missing@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "重置链接已发送"

def test_verification_code_attempt_limit(test_client):
    email = "erin@example.com"
    resp = test_client.post("/api/auth/send-verification-code", json={"email": email})
    assert resp.status_code == 200, resp.text

    for _ in range(service.VERIFICATION_CODE_MAX_ATTEMPTS):
        failed = test_client.post(
            "/api/auth/register-with-code",
            json={
                "username": "erin",
                "email": email,
                "password": "Password123",
                "code": "000000",
            },
        )
        assert failed.status_code == 400

    assert email not in service.verification_codes

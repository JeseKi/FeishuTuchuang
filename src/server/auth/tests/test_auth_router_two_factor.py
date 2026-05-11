# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy.orm import Session

from src.server.auth import service
from src.server.auth.config import auth_config
from src.server.auth.dao import LoginChallengeDAO, RefreshTokenDAO
from src.server.auth.models import User
from src.server.auth.tests._auth_router_helpers import (
    _auth_headers,
    _enable_two_factor,
    _login_user,
    _register_user,
)


def test_two_factor_login_challenge_flow(test_client, test_db_session: Session):
    _register_user(
        test_client,
        username="twofa_user",
        email="twofa_user@example.com",
    )
    login_resp = _login_user(test_client, username="twofa_user")
    access_token = login_resp.json()["access_token"]
    secret, _ = _enable_two_factor(test_client, access_token=access_token)

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "twofa_user", "password": "Password123"},
    )
    assert challenge_resp.status_code == 202, challenge_resp.text
    challenge_data = challenge_resp.json()
    assert challenge_data["requires_2fa"] is True
    assert challenge_data["challenge_type"] == "totp"

    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_data["challenge_token"],
            "code": service.generate_totp_code(secret),
        },
    )
    assert verify_resp.status_code == 200, verify_resp.text
    assert "access_token" in verify_resp.json()

    refresh_cookie = verify_resp.cookies.get("fullstack_template_refresh_token")
    assert refresh_cookie is not None
    payload = jwt.decode(
        refresh_cookie,
        auth_config.jwt_secret_key,
        algorithms=[auth_config.jwt_algorithm],
    )
    assert RefreshTokenDAO(test_db_session).get_by_jti(payload["jti"]) is not None

def test_two_factor_challenge_rejects_replay_and_expiry(
    test_client, test_db_session: Session
):
    _register_user(
        test_client,
        username="challenge_user",
        email="challenge_user@example.com",
    )
    login_resp = _login_user(test_client, username="challenge_user")
    secret, _ = _enable_two_factor(
        test_client, access_token=login_resp.json()["access_token"]
    )

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "challenge_user", "password": "Password123"},
    )
    challenge_token = challenge_resp.json()["challenge_token"]

    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_token,
            "code": service.generate_totp_code(secret),
        },
    )
    assert verify_resp.status_code == 200, verify_resp.text

    replay_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_token,
            "code": service.generate_totp_code(secret),
        },
    )
    assert replay_resp.status_code == 401
    assert "失效" in replay_resp.json()["detail"]

    expired_resp = test_client.post(
        "/api/auth/login",
        json={"username": "challenge_user", "password": "Password123"},
    )
    expired_token = expired_resp.json()["challenge_token"]
    payload = service.decode_login_challenge_token(expired_token)
    challenge = LoginChallengeDAO(test_db_session).get_by_jti(payload["jti"])
    assert challenge is not None
    challenge.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    test_db_session.commit()

    expired_verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": expired_token,
            "code": service.generate_totp_code(secret),
        },
    )
    assert expired_verify_resp.status_code == 401
    assert "过期" in expired_verify_resp.json()["detail"]

def test_two_factor_challenge_attempt_limit(test_client, monkeypatch):
    monkeypatch.setattr(auth_config, "two_factor_max_verify_attempts", 2)

    _register_user(
        test_client,
        username="attempt_user",
        email="attempt_user@example.com",
    )
    login_resp = _login_user(test_client, username="attempt_user")
    _enable_two_factor(test_client, access_token=login_resp.json()["access_token"])

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "attempt_user", "password": "Password123"},
    )
    challenge_token = challenge_resp.json()["challenge_token"]

    first_failed = test_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert first_failed.status_code == 400

    second_failed = test_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert second_failed.status_code == 401
    assert "次数过多" in second_failed.json()["detail"]

    third_failed = test_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert third_failed.status_code == 401

def test_disable_two_factor_revokes_current_session(
    test_client, test_db_session: Session
):
    _register_user(
        test_client,
        username="disable_user",
        email="disable_user@example.com",
    )
    login_resp = _login_user(test_client, username="disable_user")
    secret, _ = _enable_two_factor(
        test_client, access_token=login_resp.json()["access_token"]
    )

    test_client.cookies.clear()
    challenge_resp = test_client.post(
        "/api/auth/login",
        json={"username": "disable_user", "password": "Password123"},
    )
    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_resp.json()["challenge_token"],
            "code": service.generate_totp_code(secret),
        },
    )
    access_token = verify_resp.json()["access_token"]

    disable_resp = test_client.post(
        "/api/auth/2fa/disable",
        headers=_auth_headers(access_token),
        json={
            "password": "Password123",
            "code": service.generate_totp_code(secret),
        },
    )
    assert disable_resp.status_code == 200, disable_resp.text
    assert disable_resp.json()["message"] == "2FA 已关闭，请重新登录"

    db_user = (
        test_db_session.query(User).filter(User.username == "disable_user").first()
    )
    assert db_user is not None
    assert db_user.two_factor_enabled is False
    assert db_user.token_version == 1

    profile_resp = test_client.get(
        "/api/auth/profile", headers=_auth_headers(access_token)
    )
    assert profile_resp.status_code == 401

    refresh_resp = test_client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401

def test_backup_code_can_only_be_used_once_and_can_be_regenerated(test_client):
    _register_user(
        test_client,
        username="backup_user",
        email="backup_user@example.com",
    )
    login_resp = _login_user(test_client, username="backup_user")
    secret, backup_codes = _enable_two_factor(
        test_client, access_token=login_resp.json()["access_token"]
    )
    backup_code = backup_codes[0]

    test_client.cookies.clear()
    first_challenge = test_client.post(
        "/api/auth/login",
        json={"username": "backup_user", "password": "Password123"},
    )
    first_verify = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": first_challenge.json()["challenge_token"],
            "code": backup_code,
        },
    )
    assert first_verify.status_code == 200, first_verify.text
    access_token = first_verify.json()["access_token"]

    test_client.cookies.clear()
    second_challenge = test_client.post(
        "/api/auth/login",
        json={"username": "backup_user", "password": "Password123"},
    )
    second_verify = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": second_challenge.json()["challenge_token"],
            "code": backup_code,
        },
    )
    assert second_verify.status_code == 400

    regenerate_resp = test_client.post(
        "/api/auth/2fa/backup-codes/regenerate",
        headers=_auth_headers(access_token),
        json={
            "password": "Password123",
            "code": service.generate_totp_code(secret),
        },
    )
    assert regenerate_resp.status_code == 200, regenerate_resp.text
    regenerated_codes = regenerate_resp.json()["backup_codes"]
    assert len(regenerated_codes) == auth_config.two_factor_backup_code_count
    assert backup_code not in regenerated_codes

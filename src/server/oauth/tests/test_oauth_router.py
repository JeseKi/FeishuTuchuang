# -*- coding: utf-8 -*-
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.models import User
from src.server.oauth.dao import OAuthAccountDAO
from src.server.oauth.service import core
from src.server.providers.constants import PROVIDER_GITHUB_OAUTH, PROVIDER_GOOGLE_OAUTH
from src.server.providers.mock_server import server_host_port
from src.server.providers.runtime import (
    clear_provider_runtime_configs,
    update_provider_runtime_config,
)

FAKE_GITHUB_EMAIL = "fake-github@example.com"
FAKE_GITHUB_LOGIN = "fake_github_user"
FAKE_GITHUB_PROVIDER_USER_ID = "fake-github-10001"
FAKE_GOOGLE_EMAIL = "fake-google@example.com"
FAKE_GOOGLE_PROVIDER_USER_ID = "fake-google-10001"


class _GitHubMockHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/login/oauth/access_token":
            self.send_error(404)
            return
        self._send_json({"access_token": "mock-github-token", "token_type": "bearer"})

    def do_GET(self) -> None:
        if self.path == "/user":
            self._send_json(
                {
                    "id": FAKE_GITHUB_PROVIDER_USER_ID,
                    "login": FAKE_GITHUB_LOGIN,
                    "name": "Mock GitHub User",
                    "avatar_url": "http://mock.local/github.png",
                }
            )
            return
        if self.path == "/user/emails":
            self._send_json(
                [
                    {
                        "email": FAKE_GITHUB_EMAIL,
                        "primary": True,
                        "verified": True,
                    }
                ]
            )
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _GoogleMockHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/token":
            self.send_error(404)
            return
        self._send_json({"access_token": "mock-google-token", "token_type": "Bearer"})

    def do_GET(self) -> None:
        if self.path == "/userinfo":
            self._send_json(
                {
                    "sub": FAKE_GOOGLE_PROVIDER_USER_ID,
                    "email": FAKE_GOOGLE_EMAIL,
                    "email_verified": True,
                    "name": "Mock Google User",
                    "picture": "http://mock.local/google.png",
                }
            )
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _start_http_server(
    handler_cls: type[BaseHTTPRequestHandler],
) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server_host_port(server)
    return server, f"http://{host}:{port}"


@pytest.fixture(autouse=True)
def mock_oauth_provider_servers() -> Iterator[None]:
    github_server, github_base_url = _start_http_server(_GitHubMockHandler)
    google_server, google_base_url = _start_http_server(_GoogleMockHandler)
    update_provider_runtime_config(PROVIDER_GITHUB_OAUTH, {"base_url": github_base_url})
    update_provider_runtime_config(PROVIDER_GOOGLE_OAUTH, {"base_url": google_base_url})
    try:
        yield
    finally:
        github_server.shutdown()
        google_server.shutdown()
        github_server.server_close()
        google_server.server_close()
        clear_provider_runtime_configs()


def _extract_ticket(location: str) -> str:
    query = parse_qs(urlparse(location).query)
    ticket = query.get("oauth_ticket")
    assert ticket
    return ticket[0]


def test_oauth_providers_follow_oauth_list(test_client, monkeypatch):
    monkeypatch.setenv("OAUTH_LIST", "")
    resp = test_client.get("/api/oauth/providers")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"providers": []}

    monkeypatch.setenv("OAUTH_LIST", '["GITHUB"]')
    resp = test_client.get("/api/oauth/providers")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"providers": [{"provider": "GITHUB", "label": "GitHub"}]}

    monkeypatch.setenv("OAUTH_LIST", '["GITHUB", "GOOGLE"]')
    resp = test_client.get("/api/oauth/providers")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "providers": [
            {"provider": "GITHUB", "label": "GitHub"},
            {"provider": "GOOGLE", "label": "Google"},
        ]
    }


def test_github_oauth_disabled_returns_not_found(test_client, monkeypatch):
    monkeypatch.setenv("OAUTH_LIST", "")
    resp = test_client.get("/api/oauth/github/authorize", follow_redirects=False)
    assert resp.status_code == 404


def test_google_oauth_disabled_returns_not_found(test_client, monkeypatch):
    monkeypatch.setenv("OAUTH_LIST", "")
    resp = test_client.get("/api/oauth/google/authorize", follow_redirects=False)
    assert resp.status_code == 404


def test_github_oauth_auto_creates_user_and_ticket(
    test_client, test_db_session: Session, monkeypatch
):
    monkeypatch.setenv("OAUTH_LIST", "GITHUB")

    state = core.create_oauth_state("/dashboard")
    callback_resp = test_client.get(
        "/api/oauth/github/callback",
        params={"code": "github-code", "state": state},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307), callback_resp.text
    location = callback_resp.headers["location"]
    assert urlparse(location).path == "/login"
    assert "oauth_redirect_path=%2Fdashboard" in location

    ticket = _extract_ticket(location)
    exchange_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert exchange_resp.status_code == 200, exchange_resp.text
    assert "access_token" in exchange_resp.json()
    assert exchange_resp.cookies.get("fullstack_template_refresh_token") is not None

    user = test_db_session.query(User).filter(User.email == FAKE_GITHUB_EMAIL).first()
    assert user is not None
    assert user.username == FAKE_GITHUB_LOGIN
    account = OAuthAccountDAO(test_db_session).get_by_provider_user_id(
        "GITHUB", FAKE_GITHUB_PROVIDER_USER_ID
    )
    assert account is not None
    assert account.user_id == user.id

    replay_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert replay_resp.status_code == 401


def test_google_oauth_auto_creates_user_and_ticket(
    test_client, test_db_session: Session, monkeypatch
):
    monkeypatch.setenv("OAUTH_LIST", "GOOGLE")

    state = core.create_oauth_state("/dashboard")
    callback_resp = test_client.get(
        "/api/oauth/google/callback",
        params={"code": "google-code", "state": state},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307), callback_resp.text
    location = callback_resp.headers["location"]
    assert urlparse(location).path == "/login"
    assert "oauth_redirect_path=%2Fdashboard" in location

    ticket = _extract_ticket(location)
    exchange_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert exchange_resp.status_code == 200, exchange_resp.text
    assert "access_token" in exchange_resp.json()
    assert exchange_resp.cookies.get("fullstack_template_refresh_token") is not None

    user = test_db_session.query(User).filter(User.email == FAKE_GOOGLE_EMAIL).first()
    assert user is not None
    assert user.username == "fake_google"
    account = OAuthAccountDAO(test_db_session).get_by_provider_user_id(
        "GOOGLE", FAKE_GOOGLE_PROVIDER_USER_ID
    )
    assert account is not None
    assert account.user_id == user.id

    replay_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert replay_resp.status_code == 401


def test_github_oauth_binds_existing_user_by_email(
    test_client, test_db_session: Session, monkeypatch
):
    monkeypatch.setenv("OAUTH_LIST", "GITHUB")
    user = User(username="existing", email=FAKE_GITHUB_EMAIL, name="Existing")
    user.set_password("Password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    state = core.create_oauth_state()
    callback_resp = test_client.get(
        "/api/oauth/github/callback",
        params={"code": "github-code", "state": state},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307), callback_resp.text
    ticket = _extract_ticket(callback_resp.headers["location"])

    exchange_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert exchange_resp.status_code == 200, exchange_resp.text

    users = test_db_session.query(User).filter(User.email == FAKE_GITHUB_EMAIL).all()
    assert len(users) == 1
    account = OAuthAccountDAO(test_db_session).get_by_provider_user_id(
        "GITHUB", FAKE_GITHUB_PROVIDER_USER_ID
    )
    assert account is not None
    assert account.user_id == user.id


def test_github_oauth_requires_local_two_factor_when_enabled(
    test_client, test_db_session: Session, monkeypatch
):
    monkeypatch.setenv("OAUTH_LIST", "GITHUB")
    user = User(username="twofa_oauth", email=FAKE_GITHUB_EMAIL)
    user.set_password("Password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    secret = auth_service.generate_totp_secret()
    auth_service.enable_two_factor(
        test_db_session, user, auth_service.encrypt_totp_secret(secret)
    )

    state = core.create_oauth_state()
    callback_resp = test_client.get(
        "/api/oauth/github/callback",
        params={"code": "github-code", "state": state},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307), callback_resp.text
    ticket = _extract_ticket(callback_resp.headers["location"])

    exchange_resp = test_client.post("/api/oauth/ticket", json={"ticket": ticket})
    assert exchange_resp.status_code == 200, exchange_resp.text
    exchange_data = exchange_resp.json()
    assert exchange_data["requires_2fa"] is True
    assert exchange_data["challenge_type"] == "totp"

    verify_resp = test_client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": exchange_data["challenge_token"],
            "code": auth_service.generate_totp_code(secret),
        },
    )
    assert verify_resp.status_code == 200, verify_resp.text
    assert "access_token" in verify_resp.json()

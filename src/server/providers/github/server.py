# -*- coding: utf-8 -*-
"""GitHub OAuth mock service."""

from __future__ import annotations

import json
from html import escape
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse

from src.server.providers.constants import PROVIDER_GITHUB_OAUTH
from src.server.providers.mock_server import (
    RunningMockService,
    send_html,
    start_http_mock_service,
)


class GitHubMockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/login/oauth/authorize":
            params = parse_qs(parsed.query)
            redirect_uri = params.get("redirect_uri", [""])[0]
            state = params.get("state", [""])[0]
            client_id = params.get("client_id", [""])[0]
            scope = params.get("scope", [""])[0]
            if params.get("approve", [""])[0] == "1":
                query = urlencode({"code": "mock-github-code", "state": state})
                self.send_response(302)
                self.send_header("Location", f"{redirect_uri}?{query}")
                self.end_headers()
                return
            approve_query = urlencode(
                {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "scope": scope,
                    "state": state,
                    "approve": "1",
                }
            )
            send_html(
                self,
                title="Mock GitHub OAuth",
                body=f"""
                <h1>Mock GitHub OAuth</h1>
                <p>应用 <code>{escape(client_id)}</code> 请求访问 mock GitHub 账号。</p>
                <p>Scope: <code>{escape(scope)}</code></p>
                <p class="muted">确认后会携带 authorization code 回跳到应用 callback。</p>
                <div class="actions">
                  <a class="button" href="/login/oauth/authorize?{escape(approve_query)}">允许授权</a>
                </div>
                """,
            )
            return
        if parsed.path == "/user":
            self._send_json(
                {
                    "id": "fake-github-10001",
                    "login": "fake_github_user",
                    "name": "Mock GitHub User",
                    "avatar_url": "http://mock.local/github.png",
                }
            )
            return
        if parsed.path == "/user/emails":
            self._send_json(
                [
                    {
                        "email": "fake-github@example.com",
                        "primary": True,
                        "verified": True,
                    }
                ]
            )
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/login/oauth/access_token":
            self.send_error(404)
            return
        self._send_json(
            {
                "access_token": "mock-github-token",
                "token_type": "bearer",
                "scope": "read:user user:email",
            }
        )

    def log_message(self, format: str, *args) -> None:
        print(f"[mock-github] {self.address_string()} - {format % args}")

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start() -> RunningMockService:
    return start_http_mock_service(
        provider_key=PROVIDER_GITHUB_OAUTH,
        name="GitHub OAuth",
        handler_cls=GitHubMockHandler,
        config_factory=lambda base_url: {
            "base_url": base_url,
            "client_id": "mock-github-client",
            "client_secret": "mock-github-secret",
        },
    )

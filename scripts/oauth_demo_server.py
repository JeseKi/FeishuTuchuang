#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tiny OAuth client demo server for local testing.

Run this as a fake third-party app on http://localhost:3000.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PORT = int(os.getenv("OAUTH_DEMO_PORT", "3000"))
PROVIDER_ORIGIN = os.getenv("OAUTH_DEMO_PROVIDER_ORIGIN", "http://localhost:8000").rstrip("/")
AUTHORIZE_ORIGIN = os.getenv("OAUTH_DEMO_AUTHORIZE_ORIGIN", PROVIDER_ORIGIN).rstrip("/")
ADMIN_TOKEN = os.getenv("OAUTH_DEMO_ADMIN_TOKEN", "KISPACE_TEST_TOKEN")
REDIRECT_URI = os.getenv("OAUTH_DEMO_REDIRECT_URI", f"http://localhost:{PORT}/callback")
REQUESTED_SCOPE = os.getenv("OAUTH_DEMO_SCOPE", "profile:read")

CLIENT: dict[str, str] | None = None
PENDING_AUTH: dict[str, dict[str, str | float]] = {}
DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> dict[str, Any]:
    req = Request(url, data=body, method=method, headers=headers or {})
    with urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _request_json_with_status(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, Any]]:
    req = Request(url, data=body, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"detail": raw or exc.reason}
        return exc.code, data


def _ensure_client() -> dict[str, str]:
    global CLIENT
    if CLIENT is not None:
        return CLIENT

    payload = {
        "name": "Local curl/http.server OAuth Demo",
        "redirect_uris": [REDIRECT_URI],
        "allowed_scopes": REQUESTED_SCOPE.split(),
        "is_active": True,
        "require_pkce": True,
    }
    data = _request_json(
        "POST",
        f"{PROVIDER_ORIGIN}/api/oauth-provider/clients",
        headers={
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "Content-Type": "application/json",
        },
        body=json.dumps(payload).encode("utf-8"),
    )
    CLIENT = {
        "client_id": data["client_id"],
        "client_secret": data["client_secret"],
    }
    return CLIENT


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _exchange_code(client: dict[str, str], code: str, verifier: str) -> dict[str, Any]:
    form = urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        }
    ).encode("utf-8")
    basic = base64.b64encode(
        f"{client['client_id']}:{client['client_secret']}".encode("utf-8")
    ).decode("ascii")
    return _request_json(
        "POST",
        f"{PROVIDER_ORIGIN}/api/oauth-provider/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body=form,
    )


def _basic_auth_header(client: dict[str, str]) -> str:
    raw = f"{client['client_id']}:{client['client_secret']}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _start_device_authorization(client: dict[str, str]) -> dict[str, Any]:
    form = urlencode(
        {
            "client_id": client["client_id"],
            "scope": REQUESTED_SCOPE,
        }
    ).encode("utf-8")
    return _request_json(
        "POST",
        f"{PROVIDER_ORIGIN}/api/oauth-provider/device_authorization",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=form,
    )


def _exchange_device_code(
    client: dict[str, str],
    device_code: str,
) -> tuple[int, dict[str, Any]]:
    form = urlencode(
        {
            "grant_type": DEVICE_CODE_GRANT_TYPE,
            "device_code": device_code,
        }
    ).encode("utf-8")
    return _request_json_with_status(
        "POST",
        f"{PROVIDER_ORIGIN}/api/oauth-provider/token",
        headers={
            "Authorization": _basic_auth_header(client),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body=form,
    )


def _fetch_userinfo(access_token: str) -> dict[str, Any]:
    return _request_json(
        "GET",
        f"{PROVIDER_ORIGIN}/api/oauth-provider/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def _page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7f9; color: #1f2937; }}
    main {{ max-width: 760px; margin: 64px auto; padding: 0 20px; }}
    section {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 28px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    a.button {{ display: inline-block; background: #1677ff; color: white; text-decoration: none; padding: 10px 16px; border-radius: 6px; }}
    a.secondary {{ background: #374151; }}
    code, pre {{ background: #f3f4f6; border-radius: 6px; }}
    code {{ padding: 2px 5px; }}
    pre {{ padding: 14px; overflow: auto; }}
    .actions {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    .code {{ font-size: 28px; letter-spacing: 0.08em; font-weight: 700; }}
    .muted {{ color: #6b7280; }}
  </style>
</head>
<body><main><section>{body}</section></main></body>
</html>""".encode("utf-8")


class OAuthDemoHandler(BaseHTTPRequestHandler):
    server_version = "OAuthDemoHTTP/0.1"

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._handle_home()
            elif parsed.path == "/login":
                self._handle_login()
            elif parsed.path == "/device-login":
                self._handle_device_login()
            elif parsed.path == "/device-status":
                self._handle_device_status(parsed.query)
            elif parsed.path == "/callback":
                self._handle_callback(parsed.query)
            else:
                self.send_error(404, "Not Found")
        except Exception as exc:
            self._send_html(
                500,
                "OAuth Demo Error",
                f"<h1>OAuth Demo Error</h1><pre>{html.escape(str(exc))}</pre>",
            )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[oauth-demo] {self.address_string()} - {format % args}")

    def _handle_home(self) -> None:
        body = f"""
        <h1>OAuth Demo Client</h1>
        <p class="muted">这是一个跑在 <code>localhost:{PORT}</code> 的第三方系统模拟器。</p>
        <p>Provider: <code>{html.escape(PROVIDER_ORIGIN)}</code></p>
        <p>Authorize UI: <code>{html.escape(AUTHORIZE_ORIGIN)}/oauth/authorize</code></p>
        <p>Redirect URI: <code>{html.escape(REDIRECT_URI)}</code></p>
        <div class="actions">
          <a class="button" href="/login">Authorization Code + PKCE</a>
          <a class="button secondary" href="/device-login">Device Code Flow</a>
        </div>
        """
        self._send_html(200, "OAuth Demo Client", body)

    def _handle_login(self) -> None:
        client = _ensure_client()
        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(24)
        PENDING_AUTH[state] = {"verifier": verifier, "created_at": time.time()}
        params = urlencode(
            {
                "response_type": "code",
                "client_id": client["client_id"],
                "redirect_uri": REDIRECT_URI,
                "scope": REQUESTED_SCOPE,
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        self.send_response(302)
        self.send_header("Location", f"{AUTHORIZE_ORIGIN}/oauth/authorize?{params}")
        self.end_headers()

    def _handle_device_login(self) -> None:
        client = _ensure_client()
        device_data = _start_device_authorization(client)
        device_code = html.escape(device_data["device_code"])
        user_code = html.escape(device_data["user_code"])
        verification_uri = html.escape(device_data["verification_uri"])
        verification_uri_complete = html.escape(device_data["verification_uri_complete"])
        interval = int(device_data.get("interval", 5))
        body = f"""
        <h1>Device Code Flow</h1>
        <p class="muted">设备端已经拿到 <code>device_code</code>，现在等待用户在浏览器确认授权。</p>
        <p>用户授权码：</p>
        <p class="code">{user_code}</p>
        <p>授权地址：<code>{verification_uri}</code></p>
        <div class="actions">
          <a class="button" href="{verification_uri_complete}" target="_blank" rel="noreferrer">打开授权页面</a>
          <a class="button secondary" href="/">返回首页</a>
        </div>
        <h2>轮询状态</h2>
        <pre id="status">authorization_pending</pre>
        <script>
          const statusBox = document.getElementById('status');
          let interval = {interval * 1000};
          async function poll() {{
            const resp = await fetch('/device-status?device_code={device_code}');
            const data = await resp.json();
            statusBox.textContent = JSON.stringify(data, null, 2);
            if (data.status === 'authorized') return;
            if (data.status === 'slow_down') interval += 5000;
            window.setTimeout(poll, interval);
          }}
          window.setTimeout(poll, interval);
        </script>
        """
        self._send_html(200, "OAuth Device Demo", body)

    def _handle_device_status(self, query: str) -> None:
        params = parse_qs(query)
        device_code = params.get("device_code", [""])[0]
        if not device_code:
            self._send_json(400, {"status": "error", "detail": "missing device_code"})
            return

        client = _ensure_client()
        status_code, token_data = _exchange_device_code(client, device_code)
        if status_code == 200:
            userinfo = _fetch_userinfo(token_data["access_token"])
            self._send_json(
                200,
                {
                    "status": "authorized",
                    "userinfo": userinfo,
                    "token_response": token_data,
                },
            )
            return

        detail = str(token_data.get("detail") or "invalid_grant")
        if detail in {"authorization_pending", "slow_down", "access_denied", "expired_token"}:
            self._send_json(200, {"status": detail, "token_response": token_data})
            return
        self._send_json(status_code, {"status": "error", "token_response": token_data})

    def _handle_callback(self, query: str) -> None:
        params = parse_qs(query)
        state = params.get("state", [""])[0]
        pending = PENDING_AUTH.pop(state, None)
        if pending is None:
            self._send_html(400, "OAuth State Error", "<h1>state 无效或已过期</h1>")
            return
        if time.time() - float(pending["created_at"]) > 600:
            self._send_html(400, "OAuth State Error", "<h1>state 已过期</h1>")
            return
        if "error" in params:
            error = html.escape(params.get("error", ["access_denied"])[0])
            self._send_html(400, "OAuth Denied", f"<h1>OAuth 被拒绝</h1><pre>{error}</pre>")
            return

        code = params.get("code", [""])[0]
        if not code:
            self._send_html(400, "OAuth Callback Error", "<h1>callback 缺少 code</h1>")
            return

        client = _ensure_client()
        token_data = _exchange_code(client, code, str(pending["verifier"]))
        userinfo = _fetch_userinfo(token_data["access_token"])
        body = f"""
        <h1>OAuth 登录成功</h1>
        <p>第三方系统已经通过授权码换到了 token，并调用了 <code>/userinfo</code>。</p>
        <h2>Userinfo</h2>
        <pre>{html.escape(json.dumps(userinfo, ensure_ascii=False, indent=2))}</pre>
        <h2>Token Response</h2>
        <pre>{html.escape(json.dumps(token_data, ensure_ascii=False, indent=2))}</pre>
        <p><a class="button" href="/">返回首页</a></p>
        """
        self._send_html(200, "OAuth Success", body)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_html(self, status: int, title: str, body: str) -> None:
        content = _page(title, body)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), OAuthDemoHandler)
    print(f"OAuth demo client: http://localhost:{PORT}")
    print(f"Provider origin: {PROVIDER_ORIGIN}")
    print(f"Authorize origin: {AUTHORIZE_ORIGIN}")
    print(f"Redirect URI: {REDIRECT_URI}")
    server.serve_forever()


if __name__ == "__main__":
    main()

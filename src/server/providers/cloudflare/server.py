# -*- coding: utf-8 -*-
"""Cloudflare Turnstile mock service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

from src.server.providers.constants import PROVIDER_TURNSTILE
from src.server.providers.mock_server import RunningMockService, start_http_mock_service


class CloudflareTurnstileMockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/turnstile/v0/api.js":
            self.send_error(404)
            return
        self._send_javascript(_build_turnstile_mock_script())

    def do_POST(self) -> None:
        if self.path != "/turnstile/v0/siteverify":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(raw_body)
        token = form.get("response", [""])[0]
        action = form.get("action", [""])[0] or _extract_action_from_token(token)
        if token == "mock-fail":
            self._send_json({"success": False, "error-codes": ["invalid-input-response"]})
            return
        self._send_json(
            {
                "success": True,
                "challenge_ts": datetime.now(timezone.utc).isoformat(),
                "hostname": "localhost",
                "error-codes": [],
                "action": action,
            }
        )

    def log_message(self, format: str, *args) -> None:
        print(f"[mock-turnstile] {self.address_string()} - {format % args}")

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_javascript(self, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _extract_action_from_token(token: str) -> str:
    prefix = "mock-turnstile-token-"
    if not token.startswith(prefix):
        return "mock"
    remainder = token[len(prefix):]
    action, separator, _timestamp = remainder.rpartition("-")
    if not separator or not action:
        return "mock"
    return action


def _build_turnstile_mock_script() -> str:
    return r"""
(function () {
  var widgets = new Map();
  var nextId = 1;

  function resolveContainer(container) {
    if (typeof container === 'string') {
      return document.querySelector(container);
    }
    return container;
  }

  function render(container, options) {
    var target = resolveContainer(container);
    if (!target) {
      throw new Error('Turnstile mock container not found');
    }

    var widgetId = 'mock-turnstile-' + nextId++;
    var action = options && options.action ? String(options.action) : 'mock';
    var token = 'mock-turnstile-token-' + action + '-' + Date.now();

    target.innerHTML = '';
    var wrapper = document.createElement('div');
    wrapper.style.border = '1px solid #d0d7de';
    wrapper.style.borderRadius = '6px';
    wrapper.style.padding = '10px';
    wrapper.style.background = '#f6f8fa';
    wrapper.style.display = 'flex';
    wrapper.style.alignItems = 'center';
    wrapper.style.justifyContent = 'space-between';
    wrapper.style.gap = '12px';

    var label = document.createElement('span');
    label.textContent = '本地 Turnstile mock';
    label.style.color = '#24292f';
    label.style.fontSize = '14px';

    var button = document.createElement('button');
    button.type = 'button';
    button.textContent = '完成机器人校验';
    button.style.border = '0';
    button.style.borderRadius = '6px';
    button.style.background = '#1f6feb';
    button.style.color = '#fff';
    button.style.padding = '8px 12px';
    button.style.cursor = 'pointer';
    button.onclick = function () {
      button.textContent = '校验已完成';
      button.disabled = true;
      button.style.background = '#1f883d';
      if (options && typeof options.callback === 'function') {
        options.callback(token);
      }
    };

    wrapper.appendChild(label);
    wrapper.appendChild(button);
    target.appendChild(wrapper);
    widgets.set(widgetId, { target: target });
    return widgetId;
  }

  function remove(widgetId) {
    var widget = widgets.get(widgetId);
    if (widget && widget.target) {
      widget.target.innerHTML = '';
    }
    widgets.delete(widgetId);
  }

  function reset(widgetId) {
    var widget = widgets.get(widgetId);
    if (widget && widget.target) {
      widget.target.querySelectorAll('button').forEach(function (button) {
        button.disabled = false;
        button.textContent = '完成机器人校验';
        button.style.background = '#1f6feb';
      });
    }
  }

  window.turnstile = { render: render, remove: remove, reset: reset };
})();
"""


def start() -> RunningMockService:
    return start_http_mock_service(
        provider_key=PROVIDER_TURNSTILE,
        name="Cloudflare Turnstile",
        handler_cls=CloudflareTurnstileMockHandler,
        config_factory=lambda base_url: {
            "base_url": base_url,
            "secret_key": "mock-turnstile-secret",
            "site_key": "mock-site-key",
        },
    )

# -*- coding: utf-8 -*-
"""Example external API mock service."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from src.server.providers.constants import PROVIDER_EXAMPLE_EXTERNAL_API
from src.server.providers.mock_server import RunningMockService, start_http_mock_service


class ExampleExternalApiMockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/status":
            self.send_error(404)
            return
        self._send_json({"status": "ok", "message": "mock external API response"})

    def log_message(self, format: str, *args) -> None:
        print(f"[mock-example-api] {self.address_string()} - {format % args}")

    def _send_json(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start() -> RunningMockService:
    return start_http_mock_service(
        provider_key=PROVIDER_EXAMPLE_EXTERNAL_API,
        name="Example External API",
        handler_cls=ExampleExternalApiMockHandler,
        config_factory=lambda base_url: {"base_url": base_url},
    )

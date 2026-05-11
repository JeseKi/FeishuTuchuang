# -*- coding: utf-8 -*-
"""Utilities for local external-provider mock services."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from typing import Any, cast


@dataclass
class RunningMockService:
    provider_key: str
    name: str
    config: dict[str, Any]
    shutdown: Callable[[], None]


def server_host_port(server: TCPServer) -> tuple[str, int]:
    address = server.server_address
    if not isinstance(address, tuple) or len(address) < 2:
        raise RuntimeError("mock server did not expose an inet address")
    host = address[0]
    port = address[1]
    if not isinstance(host, str) or not isinstance(port, int):
        raise RuntimeError("mock server exposed an unsupported address")
    return host, port


def send_html(
    handler: BaseHTTPRequestHandler,
    *,
    title: str,
    body: str,
    status_code: int = 200,
) -> None:
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #f5f7fb; }}
    main {{ max-width: 760px; margin: 48px auto; padding: 0 20px; }}
    section {{ background: #fff; border: 1px solid #dbe2ef; border-radius: 8px; padding: 24px; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); }}
    h1 {{ margin: 0 0 16px; font-size: 24px; }}
    p {{ line-height: 1.6; }}
    code, pre {{ background: #f1f4f9; border-radius: 6px; }}
    code {{ padding: 2px 5px; }}
    pre {{ padding: 12px; overflow: auto; }}
    a.button, button {{ appearance: none; border: 0; background: #1f6feb; color: white; text-decoration: none; padding: 10px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; }}
    a.secondary {{ background: #57606a; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #dbe2ef; padding: 10px; text-align: left; vertical-align: top; }}
    .muted {{ color: #65758b; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }}
  </style>
</head>
<body><main><section>{body}</section></main></body>
</html>"""
    payload = html.encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def start_http_mock_service(
    *,
    provider_key: str,
    name: str,
    handler_cls: type[BaseHTTPRequestHandler],
    config_factory: Callable[[str], dict[str, Any]],
) -> RunningMockService:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server_host_port(cast(ThreadingHTTPServer, server))
    base_url = f"http://{host}:{port}"

    def _shutdown() -> None:
        server.shutdown()
        server.server_close()

    return RunningMockService(
        provider_key=provider_key,
        name=name,
        config=config_factory(base_url),
        shutdown=_shutdown,
    )

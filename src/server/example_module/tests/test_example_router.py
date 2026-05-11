# -*- coding: utf-8 -*-
import json
import re
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import HTTPStatus

import pytest

from src.server.providers.constants import PROVIDER_EXAMPLE_EXTERNAL_API
from src.server.providers.mock_server import server_host_port
from src.server.providers.runtime import (
    clear_provider_runtime_configs,
    update_provider_runtime_config,
)

TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{32}$")


class _ExampleApiMockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/status":
            self.send_error(404)
            return
        body = json.dumps(
            {"status": "ok", "message": "mock external API response"}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


@pytest.fixture
def example_api_mock_server() -> Iterator[None]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ExampleApiMockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server_host_port(server)
    update_provider_runtime_config(
        PROVIDER_EXAMPLE_EXTERNAL_API,
        {"base_url": f"http://{host}:{port}"},
    )
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        clear_provider_runtime_configs()


def _login_admin(test_client):
    """登录默认管理员用户并返回认证头"""
    resp = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    access_token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_ping(test_client):
    resp = test_client.get("/api/example/ping")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["message"] == "pong"


def test_create_and_get_item(test_client, init_test_database):
    # 登录获取认证头
    headers = _login_admin(test_client)

    # 创建
    resp = test_client.post(
        "/api/example/items",
        json={"name": "hello"},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    item = resp.json()

    # 重复名称
    resp2 = test_client.post(
        "/api/example/items",
        json={"name": "hello"},
        headers=headers,
    )
    assert resp2.status_code == HTTPStatus.BAD_REQUEST

    # 查询
    resp3 = test_client.get(
        f"/api/example/items/{item['id']}",
        headers=headers,
    )
    assert resp3.status_code == HTTPStatus.OK
    assert resp3.json()["name"] == "hello"

    # 查询不存在
    resp4 = test_client.get(
        "/api/example/items/999999",
        headers=headers,
    )
    assert resp4.status_code == HTTPStatus.NOT_FOUND


def test_create_and_get_async_task(test_client, init_test_database):
    headers = _login_admin(test_client)

    create_resp = test_client.post(
        "/api/example/tasks",
        json={
            "name": "batch-import",
            "total_count": 6,
            "fail_every": 3,
            "delay_ms": 0,
        },
        headers=headers,
    )
    assert create_resp.status_code == HTTPStatus.ACCEPTED, create_resp.text
    task = create_resp.json()
    assert task["name"] == "batch-import"
    assert TASK_ID_PATTERN.fullmatch(task["id"])

    detail_resp = test_client.get(
        f"/api/example/tasks/{task['id']}",
        headers=headers,
    )
    assert detail_resp.status_code == HTTPStatus.OK, detail_resp.text

    detail = detail_resp.json()
    assert detail["status"] == "completed"
    assert detail["processed_count"] == 6
    assert detail["success_count"] == 4
    assert detail["failure_count"] == 2
    assert detail["progress_percent"] == 100
    assert len(detail["logs"]) == 9
    assert detail["logs"][0]["message"] == "任务已创建，总计 6 项待处理。"
    assert detail["logs"][-1]["message"] == "任务执行完成，成功 4 项，失败 2 项。"


def test_external_status_uses_mock_provider(
    test_client, init_test_database, example_api_mock_server
):
    headers = _login_admin(test_client)

    resp = test_client.get("/api/example/external/status", headers=headers)

    assert resp.status_code == HTTPStatus.OK, resp.text
    assert resp.json() == {
        "provider": "mock",
        "status": "ok",
        "message": "mock external API response",
    }


def test_unauthenticated_access(test_client):
    """测试未认证的访问被拒绝"""
    # 尝试不带认证头创建
    resp = test_client.post("/api/example/items", json={"name": "test"})
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

    # 尝试不带认证头查询
    resp = test_client.get("/api/example/items/1")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

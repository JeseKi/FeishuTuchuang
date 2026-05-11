# -*- coding: utf-8 -*-
"""
pytest 公共 fixtures（模板版）

功能：
- 统一测试环境变量
- 提供内存 SQLite 的数据库引擎、会话与 TestClient
- 引导默认管理员

公开接口：
- `test_db_engine`
- `test_db_session`
- `test_client`
- `init_test_database`
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Connection

# 测试环境配置
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')
os.environ["TURNSTILE_ENABLED"] = "false"
os.environ.setdefault(
    "EXTERNAL_PROVIDER_MOCK_LIST",
    '["github_oauth", "google_oauth", "turnstile", "mail", "example_external_api"]',
)


class SyncASGITestClient:
    """为同步 pytest 用例提供基于 httpx 的最小 ASGI client 包装。"""

    def __init__(self, app):
        self._loop = asyncio.new_event_loop()
        self._transport = httpx.ASGITransport(app=app)
        self._client = httpx.AsyncClient(
            transport=self._transport,
            base_url="http://testserver",
            follow_redirects=True,
        )

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    def get(self, *args, **kwargs):
        return self._run(self._client.get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return self._run(self._client.post(*args, **kwargs))

    def put(self, *args, **kwargs):
        return self._run(self._client.put(*args, **kwargs))

    def patch(self, *args, **kwargs):
        return self._run(self._client.patch(*args, **kwargs))

    def delete(self, *args, **kwargs):
        return self._run(self._client.delete(*args, **kwargs))

    @property
    def cookies(self):
        return self._client.cookies

    def close(self) -> None:
        self._run(self._client.aclose())
        self._loop.close()


@pytest.fixture(autouse=True)
def disable_real_mail_delivery(monkeypatch: pytest.MonkeyPatch) -> None:
    """测试期间统一禁用真实邮件发送，避免连接外部 SMTP。"""
    from src.server.mail.config import mail_config

    monkeypatch.setattr(mail_config, "sender_email", None, raising=False)
    monkeypatch.setattr(mail_config, "sender_password", None, raising=False)


@pytest.fixture(scope="function")
def test_db_engine() -> Iterator[Connection]:
    """提供共享内存 SQLite 连接（保持连接存活，保证多线程一致）。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    keep_conn = engine.connect()

    from src.server.database import Base
    import src.server.auth.models  # noqa: F401
    import src.server.example_module.models  # noqa: F401
    import src.server.scope_management.models  # noqa: F401
    import src.server.oauth.models  # noqa: F401
    import src.server.oauth_provider.models  # noqa: F401
    import src.server.providers.models  # noqa: F401

    Base.metadata.create_all(bind=keep_conn)

    TestingSessionLocal = sessionmaker(
        bind=keep_conn, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        from src.server.providers.service import sync_external_providers

        sync_external_providers(session)
    finally:
        session.close()

    try:
        yield keep_conn
    finally:
        try:
            keep_conn.close()
        finally:
            engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Iterator[Session]:
    """提供内存数据库会话。"""
    TestingSessionLocal = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session: Session) -> Iterator[SyncASGITestClient]:
    """提供一个配置了测试数据库的 FastAPI TestClient。"""
    from src.server.main import app
    from src.server.database import get_db

    async def override_get_db() -> AsyncIterator[Session]:
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    client = SyncASGITestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def init_test_database(test_db_engine) -> None:
    """初始化默认管理员等必要基础数据。"""
    TestingSessionLocal = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()
    try:
        from src.server.auth.models import User
        from src.server.auth.schemas import UserRole

        exists = session.query(User).order_by(User.id.asc()).first()
        if not exists:
            admin = User(
                username="admin",
                email="admin@example.com",
                name="默认管理员",
                role=UserRole.ADMIN,
            )
            admin.set_password("admin123")
            session.add(admin)
            session.commit()
    finally:
        session.close()

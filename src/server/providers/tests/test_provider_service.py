# -*- coding: utf-8 -*-
"""External provider registry tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.providers.constants import (
    PROVIDER_EXAMPLE_EXTERNAL_API,
    PROVIDER_GITHUB_OAUTH,
    PROVIDER_MAIL,
)
from src.server.providers.dao import ExternalProviderDAO
from src.server.providers.service import (
    get_example_external_api_provider,
    get_github_oauth_provider,
    get_mail_provider,
    sync_external_providers,
)
from src.server.providers.runtime import update_provider_runtime_config
from src.server.providers.cloudflare.server import _extract_action_from_token


def test_sync_external_providers_uses_env_mock_list(
    test_db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "EXTERNAL_PROVIDER_MOCK_LIST",
        '["github_oauth", "mail", "example_external_api"]',
    )
    update_provider_runtime_config(PROVIDER_GITHUB_OAUTH, {"base_url": "http://127.0.0.1:1"})
    update_provider_runtime_config(PROVIDER_MAIL, {"smtp_host": "127.0.0.1", "smtp_port": 1025})
    update_provider_runtime_config(PROVIDER_EXAMPLE_EXTERNAL_API, {"base_url": "http://127.0.0.1:2"})

    sync_external_providers(test_db_session)

    dao = ExternalProviderDAO(test_db_session)
    github = dao.get_by_key(PROVIDER_GITHUB_OAUTH)
    mail = dao.get_by_key(PROVIDER_MAIL)
    example = dao.get_by_key(PROVIDER_EXAMPLE_EXTERNAL_API)

    assert github is not None
    assert github.implementation == "mock"
    assert mail is not None
    assert mail.implementation == "mock"
    assert example is not None
    assert example.implementation == "mock"

    assert get_github_oauth_provider().implementation == "mock"
    assert get_mail_provider().implementation == "mock"
    assert get_example_external_api_provider().implementation == "mock"


def test_sync_external_providers_can_select_real_provider(
    test_db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXTERNAL_PROVIDER_MOCK_LIST", "unused_provider")

    sync_external_providers(test_db_session)

    dao = ExternalProviderDAO(test_db_session)
    github = dao.get_by_key(PROVIDER_GITHUB_OAUTH)

    assert github is not None
    assert github.implementation == "real"
    assert get_github_oauth_provider().implementation == "real"


def test_turnstile_mock_extracts_action_from_token() -> None:
    token = "mock-turnstile-token-auth_login-1760000000000"

    assert _extract_action_from_token(token) == "auth_login"
    assert _extract_action_from_token("invalid") == "mock"

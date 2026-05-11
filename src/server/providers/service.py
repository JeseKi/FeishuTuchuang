# -*- coding: utf-8 -*-
"""External provider registry service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.config import global_config

from .base import ProviderImplementation
from .constants import (
    PROVIDER_DEFINITIONS,
    PROVIDER_EXAMPLE_EXTERNAL_API,
    PROVIDER_GITHUB_OAUTH,
    PROVIDER_GOOGLE_OAUTH,
    PROVIDER_MAIL,
    PROVIDER_TURNSTILE,
)
from .dao import ExternalProviderDAO
from .example_external_api.api import (
    ExampleExternalApiProvider,
    MockExampleExternalApiProvider,
    RealExampleExternalApiProvider,
)
from .smtp.mail import MailProvider, MockMailProvider, RealMailProvider
from .github.oauth import (
    GitHubOAuthProvider,
    MockGitHubOAuthProvider,
    RealGitHubOAuthProvider,
)
from .google.oauth import (
    GoogleOAuthProvider,
    MockGoogleOAuthProvider,
    RealGoogleOAuthProvider,
)
from .cloudflare.turnstile import (
    MockTurnstileProvider,
    RealTurnstileProvider,
    TurnstileProvider,
)

_provider_modes: dict[str, ProviderImplementation] = {}


def _normalize_implementation(value: str) -> ProviderImplementation | None:
    if value == "real":
        return "real"
    if value == "mock":
        return "mock"
    return None


def sync_external_providers(db: Session) -> None:
    """Synchronize built-in provider definitions into the database."""

    dao = ExternalProviderDAO(db)
    mock_keys = set(global_config.external_provider_mock_list)
    next_modes: dict[str, ProviderImplementation] = {}

    for definition in PROVIDER_DEFINITIONS:
        implementation: ProviderImplementation = (
            "mock" if definition.key in mock_keys else "real"
        )
        dao.upsert(
            key=definition.key,
            label=definition.label,
            kind=definition.kind,
            implementation=implementation,
            is_enabled=True,
            settings_json="{}",
        )
        next_modes[definition.key] = implementation

    _provider_modes.clear()
    _provider_modes.update(next_modes)


def load_provider_modes(db: Session) -> None:
    """Load provider implementation modes from database records."""

    dao = ExternalProviderDAO(db)
    next_modes: dict[str, ProviderImplementation] = {}
    for record in dao.list_all():
        implementation = _normalize_implementation(record.implementation)
        if implementation is not None:
            next_modes[record.key] = implementation
    _provider_modes.clear()
    _provider_modes.update(next_modes)


def _mode_for(key: str) -> ProviderImplementation:
    if key in global_config.external_provider_mock_list:
        return "mock"
    mode = _provider_modes.get(key)
    if mode in ("real", "mock"):
        return mode
    return "real"


def get_github_oauth_provider() -> GitHubOAuthProvider:
    if _mode_for(PROVIDER_GITHUB_OAUTH) == "mock":
        return MockGitHubOAuthProvider()
    return RealGitHubOAuthProvider()


def get_google_oauth_provider() -> GoogleOAuthProvider:
    if _mode_for(PROVIDER_GOOGLE_OAUTH) == "mock":
        return MockGoogleOAuthProvider()
    return RealGoogleOAuthProvider()


def get_turnstile_provider() -> TurnstileProvider:
    if _mode_for(PROVIDER_TURNSTILE) == "mock":
        return MockTurnstileProvider()
    return RealTurnstileProvider()


def get_mail_provider() -> MailProvider:
    if _mode_for(PROVIDER_MAIL) == "mock":
        return MockMailProvider()
    return RealMailProvider()


def get_example_external_api_provider() -> ExampleExternalApiProvider:
    if _mode_for(PROVIDER_EXAMPLE_EXTERNAL_API) == "mock":
        return MockExampleExternalApiProvider()
    return RealExampleExternalApiProvider()

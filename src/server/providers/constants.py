# -*- coding: utf-8 -*-
"""Provider keys and registration metadata."""

from __future__ import annotations

from dataclasses import dataclass

PROVIDER_GITHUB_OAUTH = "github_oauth"
PROVIDER_GOOGLE_OAUTH = "google_oauth"
PROVIDER_TURNSTILE = "turnstile"
PROVIDER_MAIL = "mail"
PROVIDER_EXAMPLE_EXTERNAL_API = "example_external_api"

ALL_PROVIDER_KEYS = (
    PROVIDER_GITHUB_OAUTH,
    PROVIDER_GOOGLE_OAUTH,
    PROVIDER_TURNSTILE,
    PROVIDER_MAIL,
    PROVIDER_EXAMPLE_EXTERNAL_API,
)


@dataclass(frozen=True)
class ProviderDefinition:
    key: str
    label: str
    kind: str


PROVIDER_DEFINITIONS = (
    ProviderDefinition(PROVIDER_GITHUB_OAUTH, "GitHub OAuth", "oauth"),
    ProviderDefinition(PROVIDER_GOOGLE_OAUTH, "Google OAuth", "oauth"),
    ProviderDefinition(PROVIDER_TURNSTILE, "Cloudflare Turnstile", "captcha"),
    ProviderDefinition(PROVIDER_MAIL, "SMTP Mail", "mail"),
    ProviderDefinition(PROVIDER_EXAMPLE_EXTERNAL_API, "Example External API", "api"),
)

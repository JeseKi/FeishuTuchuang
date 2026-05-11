# -*- coding: utf-8 -*-
"""External provider boundary."""

from .service import (
    get_example_external_api_provider,
    get_github_oauth_provider,
    get_google_oauth_provider,
    get_mail_provider,
    get_turnstile_provider,
    sync_external_providers,
)

__all__ = [
    "get_example_external_api_provider",
    "get_github_oauth_provider",
    "get_google_oauth_provider",
    "get_mail_provider",
    "get_turnstile_provider",
    "sync_external_providers",
]

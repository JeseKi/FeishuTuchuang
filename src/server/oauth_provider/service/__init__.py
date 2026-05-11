# -*- coding: utf-8 -*-
"""OAuth Provider service."""

from .authorization import create_authorization_redirect, get_authorize_metadata
from .clients import (
    create_client,
    delete_client,
    list_clients,
    reset_client_secret,
    update_client,
)
from .constants import (
    ACCESS_TOKEN_TTL_MINUTES,
    AUTHORIZATION_CODE_TTL_MINUTES,
    REFRESH_TOKEN_TTL_DAYS,
    TOKEN_TYPE_EXTERNAL_ACCESS,
    TOKEN_TYPE_EXTERNAL_REFRESH,
    DEVICE_CODE_INTERVAL_SECONDS,
    DEVICE_CODE_TTL_MINUTES,
)
from .crypto import hash_secret, verify_secret
from .device import (
    DEVICE_CODE_GRANT_TYPE,
    confirm_device_authorization,
    create_device_authorization,
    exchange_device_code,
    get_device_authorization_metadata,
)
from .errors import OAuthProviderError
from .tokens import (
    exchange_authorization_code,
    issue_external_token_pair,
    refresh_external_token,
    revoke_token,
)
from .userinfo import get_userinfo_from_token

__all__ = [
    "ACCESS_TOKEN_TTL_MINUTES",
    "AUTHORIZATION_CODE_TTL_MINUTES",
    "DEVICE_CODE_GRANT_TYPE",
    "DEVICE_CODE_INTERVAL_SECONDS",
    "DEVICE_CODE_TTL_MINUTES",
    "OAuthProviderError",
    "REFRESH_TOKEN_TTL_DAYS",
    "TOKEN_TYPE_EXTERNAL_ACCESS",
    "TOKEN_TYPE_EXTERNAL_REFRESH",
    "create_authorization_redirect",
    "create_client",
    "create_device_authorization",
    "delete_client",
    "confirm_device_authorization",
    "exchange_authorization_code",
    "exchange_device_code",
    "get_authorize_metadata",
    "get_device_authorization_metadata",
    "get_userinfo_from_token",
    "hash_secret",
    "issue_external_token_pair",
    "list_clients",
    "refresh_external_token",
    "reset_client_secret",
    "revoke_token",
    "update_client",
    "verify_secret",
]

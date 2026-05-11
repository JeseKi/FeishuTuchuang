# -*- coding: utf-8 -*-
"""TOTP core functionality."""

from __future__ import annotations

from base64 import b32encode
from datetime import datetime
import hmac
import secrets
from urllib.parse import quote

from ...config import auth_config
from .constants import TOTP_DIGITS, TOTP_PERIOD_SECONDS, TOTP_SECRET_BYTES
from .helpers import _normalize_code, _normalize_totp_secret, _hotp_value, _utcnow


def generate_totp_secret() -> str:
    return b32encode(secrets.token_bytes(TOTP_SECRET_BYTES)).decode("ascii").rstrip("=")


def generate_totp_code(secret: str, for_time: datetime | None = None) -> str:
    active_time = for_time or _utcnow()
    counter = int(active_time.timestamp() // TOTP_PERIOD_SECONDS)
    return _hotp_value(secret, counter)


def verify_totp_code(
    secret: str,
    code: str,
    for_time: datetime | None = None,
    valid_window: int = 1,
) -> bool:
    normalized_code = _normalize_code(code)
    if not normalized_code.isdigit() or len(normalized_code) != TOTP_DIGITS:
        return False

    active_time = for_time or _utcnow()
    counter = int(active_time.timestamp() // TOTP_PERIOD_SECONDS)
    for offset in range(-valid_window, valid_window + 1):
        if hmac.compare_digest(_hotp_value(secret, counter + offset), normalized_code):
            return True
    return False


def build_otpauth_uri(secret: str, account_name: str) -> str:
    issuer = auth_config.two_factor_issuer_name
    label = quote(f"{issuer}:{account_name}")
    quoted_issuer = quote(issuer)
    return (
        f"otpauth://totp/{label}"
        f"?secret={quote(_normalize_totp_secret(secret))}"
        f"&issuer={quoted_issuer}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD_SECONDS}"
    )


def mask_totp_secret(secret: str) -> str:
    normalized = _normalize_totp_secret(secret)
    if len(normalized) <= 8:
        return normalized
    return f"{normalized[:4]}...{normalized[-4:]}"

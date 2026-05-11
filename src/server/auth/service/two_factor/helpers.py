# -*- coding: utf-8 -*-
"""Two Factor utility helper functions."""

from __future__ import annotations

from base64 import b32decode
from datetime import datetime, timezone
import hashlib
import hmac

from ...config import auth_config
from .constants import TOTP_DIGITS


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _normalize_totp_secret(secret: str) -> str:
    return secret.strip().replace(" ", "").upper()


def _normalize_code(code: str) -> str:
    return code.strip().replace(" ", "")


def normalize_backup_code(code: str) -> str:
    normalized = _normalize_code(code).replace("-", "").upper()
    return "".join(ch for ch in normalized if ch.isalnum())


def _decode_secret_bytes(secret: str) -> bytes:
    normalized = _normalize_totp_secret(secret)
    padding = "=" * (-len(normalized) % 8)
    return b32decode(normalized + padding, casefold=True)


def _hotp_value(secret: str, counter: int) -> str:
    key = _decode_secret_bytes(secret)
    message = counter.to_bytes(8, "big")
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = (
        ((digest[offset] & 0x7F) << 24)
        | (digest[offset + 1] << 16)
        | (digest[offset + 2] << 8)
        | digest[offset + 3]
    )
    value = binary % (10**TOTP_DIGITS)
    return f"{value:0{TOTP_DIGITS}d}"


def _derive_encryption_keys() -> tuple[bytes, bytes]:
    master_key = hashlib.sha256(
        auth_config.two_factor_encryption_key.encode("utf-8")
    ).digest()
    encryption_key = hmac.new(master_key, b"enc", hashlib.sha256).digest()
    mac_key = hmac.new(master_key, b"mac", hashlib.sha256).digest()
    return encryption_key, mac_key


def _build_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(block) for block in blocks) < length:
        blocks.append(
            hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        )
        counter += 1
    return b"".join(blocks)[:length]

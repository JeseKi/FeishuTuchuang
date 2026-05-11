# -*- coding: utf-8 -*-
"""Backup code generation and verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from ...config import auth_config
from .constants import (
    BACKUP_CODE_ALPHABET,
    BACKUP_CODE_HASH_ITERATIONS,
    BACKUP_CODE_SEGMENT_COUNT,
    BACKUP_CODE_SEGMENT_LENGTH,
)
from .helpers import normalize_backup_code


def generate_backup_codes(count: int | None = None) -> list[str]:
    total = count or auth_config.two_factor_backup_code_count
    codes: list[str] = []
    while len(codes) < total:
        parts = [
            "".join(
                secrets.choice(BACKUP_CODE_ALPHABET)
                for _ in range(BACKUP_CODE_SEGMENT_LENGTH)
            )
            for _ in range(BACKUP_CODE_SEGMENT_COUNT)
        ]
        code = "-".join(parts)
        if code not in codes:
            codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    normalized = normalize_backup_code(code)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt,
        BACKUP_CODE_HASH_ITERATIONS,
    )
    return f"{salt.hex()}:{digest.hex()}"


def verify_backup_code(code: str, code_hash: str) -> bool:
    normalized = normalize_backup_code(code)
    try:
        salt_hex, digest_hex = code_hash.split(":", 1)
    except ValueError:
        return False

    derived_digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        bytes.fromhex(salt_hex),
        BACKUP_CODE_HASH_ITERATIONS,
    )
    return hmac.compare_digest(derived_digest.hex(), digest_hex)

# -*- coding: utf-8 -*-
"""TOTP secret encryption and decryption."""

from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
import hashlib
import hmac
import secrets

from .constants import ENCRYPTION_VERSION, TwoFactorError
from .helpers import _build_keystream, _derive_encryption_keys, _normalize_totp_secret


def encrypt_totp_secret(secret: str) -> str:
    plaintext = _normalize_totp_secret(secret).encode("utf-8")
    encryption_key, mac_key = _derive_encryption_keys()
    nonce = secrets.token_bytes(16)
    keystream = _build_keystream(encryption_key, nonce, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
    tag = hmac.new(
        mac_key, ENCRYPTION_VERSION + nonce + ciphertext, hashlib.sha256
    ).digest()
    payload = ENCRYPTION_VERSION + nonce + tag + ciphertext
    return urlsafe_b64encode(payload).decode("ascii")


def decrypt_totp_secret(value: str) -> str:
    try:
        payload = urlsafe_b64decode(value.encode("ascii"))
    except Exception as exc:
        raise TwoFactorError("2FA secret 解密失败") from exc

    min_length = len(ENCRYPTION_VERSION) + 16 + 32
    if len(payload) < min_length or payload[:2] != ENCRYPTION_VERSION:
        raise TwoFactorError("2FA secret 解密失败")

    nonce = payload[2:18]
    tag = payload[18:50]
    ciphertext = payload[50:]
    encryption_key, mac_key = _derive_encryption_keys()
    expected_tag = hmac.new(
        mac_key, ENCRYPTION_VERSION + nonce + ciphertext, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise TwoFactorError("2FA secret 解密失败")

    keystream = _build_keystream(encryption_key, nonce, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    return plaintext.decode("utf-8")

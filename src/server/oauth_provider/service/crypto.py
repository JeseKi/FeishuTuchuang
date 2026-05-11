# -*- coding: utf-8 -*-
"""OAuth Provider crypto helpers."""

import base64
import hashlib
import hmac


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(raw_secret: str, secret_hash: str) -> bool:
    return hmac.compare_digest(hash_secret(raw_secret), secret_hash)


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return hmac.compare_digest(expected, code_challenge)

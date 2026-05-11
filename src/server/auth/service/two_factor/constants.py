# -*- coding: utf-8 -*-
"""Two Factor constants and error class."""

from __future__ import annotations

TOTP_PERIOD_SECONDS = 30
TOTP_DIGITS = 6
TOTP_SECRET_BYTES = 20
BACKUP_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
BACKUP_CODE_SEGMENT_LENGTH = 4
BACKUP_CODE_SEGMENT_COUNT = 2
BACKUP_CODE_HASH_ITERATIONS = 120_000
TOKEN_TYPE_SETUP = "two_factor_setup"
ENCRYPTION_VERSION = b"v1"


class TwoFactorError(ValueError):
    """2FA 相关的业务错误。"""

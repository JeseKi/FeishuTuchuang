# -*- coding: utf-8 -*-
"""Two Factor authentication service."""

from __future__ import annotations

from .constants import TOKEN_TYPE_SETUP, TwoFactorError
from .helpers import normalize_backup_code
from .totp import (
    build_otpauth_uri,
    generate_totp_code,
    generate_totp_secret,
    mask_totp_secret,
    verify_totp_code,
)
from .encryption import decrypt_totp_secret, encrypt_totp_secret
from .backup_codes import (
    generate_backup_codes,
    hash_backup_code,
    verify_backup_code,
)
from .service import (
    assert_password_verified,
    assert_setup_code_valid,
    assert_two_factor_can_be_managed,
    assert_valid_two_factor_code,
    create_two_factor_setup_token,
    disable_two_factor,
    enable_two_factor,
    get_active_backup_codes,
    is_two_factor_enabled,
    replace_backup_codes,
    resolve_setup_secret,
    verify_user_two_factor_code,
)

__all__ = [
    "TOKEN_TYPE_SETUP",
    "TwoFactorError",
    "normalize_backup_code",
    "build_otpauth_uri",
    "generate_totp_code",
    "generate_totp_secret",
    "mask_totp_secret",
    "verify_totp_code",
    "decrypt_totp_secret",
    "encrypt_totp_secret",
    "generate_backup_codes",
    "hash_backup_code",
    "verify_backup_code",
    "assert_password_verified",
    "assert_setup_code_valid",
    "assert_two_factor_can_be_managed",
    "assert_valid_two_factor_code",
    "create_two_factor_setup_token",
    "disable_two_factor",
    "enable_two_factor",
    "get_active_backup_codes",
    "is_two_factor_enabled",
    "replace_backup_codes",
    "resolve_setup_secret",
    "verify_user_two_factor_code",
]

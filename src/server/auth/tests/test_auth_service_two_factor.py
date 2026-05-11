# -*- coding: utf-8 -*-
"""认证服务二步验证测试。"""

from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.service import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_backup_codes,
    generate_totp_code,
    generate_totp_secret,
    hash_backup_code,
    is_two_factor_enabled,
    verify_backup_code,
    verify_totp_code,
)


def test_totp_secret_round_trip_and_code_verification():
    secret = generate_totp_secret()
    encrypted = encrypt_totp_secret(secret)

    assert decrypt_totp_secret(encrypted) == secret

    code = generate_totp_code(secret)
    assert verify_totp_code(secret, code) is True
    assert verify_totp_code(secret, "000000") is False


def test_backup_codes_are_hashed_and_verifiable():
    codes = generate_backup_codes(3)

    assert len(codes) == 3
    assert len(set(codes)) == 3

    code_hash = hash_backup_code(codes[0])
    assert verify_backup_code(codes[0], code_hash) is True
    assert verify_backup_code(codes[1], code_hash) is False


def test_is_two_factor_enabled_requires_confirmed_secret(test_db_session: Session):
    user = User(username="twofa", email="twofa@example.com")
    user.set_password("password123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    assert is_two_factor_enabled(user) is False

    user.two_factor_enabled = True
    user.two_factor_secret_encrypted = encrypt_totp_secret(generate_totp_secret())
    test_db_session.commit()
    test_db_session.refresh(user)

    assert is_two_factor_enabled(user) is True

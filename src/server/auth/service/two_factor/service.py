# -*- coding: utf-8 -*-
"""Two Factor user service functions."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ...config import auth_config
from ...dao import BackupCodeDAO, UserDAO
from ...models import BackupCode, User
from .constants import TOKEN_TYPE_SETUP, TwoFactorError
from .backup_codes import generate_backup_codes, hash_backup_code
from .encryption import decrypt_totp_secret
from .helpers import _utcnow
from .totp import verify_totp_code


def is_two_factor_enabled(user: User) -> bool:
    return bool(user.two_factor_enabled and user.two_factor_secret_encrypted)


def create_two_factor_setup_token(user: User, encrypted_secret: str) -> str:
    expires_at = _utcnow() + timedelta(minutes=auth_config.two_factor_setup_ttl_minutes)
    return jwt.encode(
        {
            "sub": str(user.id),
            "type": TOKEN_TYPE_SETUP,
            "secret": encrypted_secret,
            "exp": expires_at,
        },
        auth_config.jwt_secret_key,
        algorithm=auth_config.jwt_algorithm,
    )


def resolve_setup_secret(setup_token: str, user: User) -> str:
    try:
        payload: dict[str, Any] = jwt.decode(
            setup_token,
            auth_config.jwt_secret_key,
            algorithms=[auth_config.jwt_algorithm],
        )
    except JWTError as exc:
        raise TwoFactorError("2FA 绑定已失效，请重新开始") from exc

    if payload.get("type") != TOKEN_TYPE_SETUP:
        raise TwoFactorError("2FA 绑定已失效，请重新开始")
    if payload.get("sub") != str(user.id):
        raise TwoFactorError("2FA 绑定用户不匹配")

    encrypted_secret = payload.get("secret")
    if not isinstance(encrypted_secret, str) or not encrypted_secret:
        raise TwoFactorError("2FA 绑定已失效，请重新开始")
    return encrypted_secret


def replace_backup_codes(db: Session, user: User) -> list[str]:
    plain_codes = generate_backup_codes()
    code_hashes = [hash_backup_code(code) for code in plain_codes]
    backup_code_dao = BackupCodeDAO(db)
    backup_code_dao.delete_all_for_user(user.id)
    backup_code_dao.create_many(user.id, code_hashes)
    return plain_codes


def enable_two_factor(
    db: Session, user: User, encrypted_secret: str, confirmed_at: datetime | None = None
) -> tuple[User, list[str]]:
    confirmed_time = confirmed_at or _utcnow()
    managed_user = UserDAO(db).update(
        user,
        two_factor_enabled=True,
        two_factor_secret_encrypted=encrypted_secret,
        two_factor_confirmed_at=confirmed_time,
    )
    backup_codes = replace_backup_codes(db, managed_user)
    return managed_user, backup_codes


def disable_two_factor(db: Session, user: User) -> User:
    BackupCodeDAO(db).delete_all_for_user(user.id)
    return UserDAO(db).update(
        user,
        two_factor_enabled=False,
        two_factor_secret_encrypted=None,
        two_factor_confirmed_at=None,
    )


def verify_user_two_factor_code(db: Session, user: User, code: str) -> str | None:
    if not is_two_factor_enabled(user):
        return None

    encrypted_secret = user.two_factor_secret_encrypted
    if not encrypted_secret:
        return None

    secret = decrypt_totp_secret(encrypted_secret)
    if verify_totp_code(secret, code):
        return "totp"

    backup_code_dao = BackupCodeDAO(db)
    for backup_code in backup_code_dao.list_active_for_user(user.id):
        from .backup_codes import verify_backup_code

        if verify_backup_code(code, backup_code.code_hash):
            backup_code_dao.mark_used(backup_code)
            return "backup_code"
    return None


def get_active_backup_codes(db: Session, user: User) -> list[BackupCode]:
    return BackupCodeDAO(db).list_active_for_user(user.id)


def assert_two_factor_can_be_managed(user: User) -> None:
    if not is_two_factor_enabled(user):
        raise TwoFactorError("当前账号未开启 2FA")


def assert_password_verified(user: User, password: str) -> None:
    if not user.check_password(password):
        raise TwoFactorError("密码错误")


def assert_valid_two_factor_code(db: Session, user: User, code: str) -> str:
    verified_with = verify_user_two_factor_code(db, user, code)
    if verified_with is None:
        raise TwoFactorError("验证码或 backup code 错误")
    return verified_with


def assert_setup_code_valid(setup_token: str, user: User, code: str) -> str:
    encrypted_secret = resolve_setup_secret(setup_token, user)
    secret = decrypt_totp_secret(encrypted_secret)
    if not verify_totp_code(secret, code):
        raise TwoFactorError("TOTP 验证码错误")
    return encrypted_secret

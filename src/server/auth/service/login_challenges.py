# -*- coding: utf-8 -*-
"""2FA 登录挑战服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import auth_config
from ..dao import LoginChallengeDAO
from ..models import LoginChallenge, User

TOKEN_TYPE_LOGIN_CHALLENGE = "two_factor_login_challenge"


class LoginChallengeError(ValueError):
    """登录挑战无效、过期或不可继续使用。"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def begin_login_challenge(db: Session, user: User) -> str:
    expires_at = _utcnow() + timedelta(
        minutes=auth_config.two_factor_challenge_ttl_minutes
    )
    challenge_jti = secrets.token_urlsafe(24)
    LoginChallengeDAO(db).create(
        user_id=user.id,
        challenge_jti=challenge_jti,
        expires_at=expires_at,
    )
    return jwt.encode(
        {
            "sub": str(user.id),
            "jti": challenge_jti,
            "type": TOKEN_TYPE_LOGIN_CHALLENGE,
            "exp": expires_at,
        },
        auth_config.jwt_secret_key,
        algorithm=auth_config.jwt_algorithm,
    )


def decode_login_challenge_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            auth_config.jwt_secret_key,
            algorithms=[auth_config.jwt_algorithm],
        )
    except JWTError as exc:
        raise LoginChallengeError("登录挑战无效或已过期") from exc

    if payload.get("type") != TOKEN_TYPE_LOGIN_CHALLENGE:
        raise LoginChallengeError("登录挑战无效或已过期")
    return payload


def get_valid_login_challenge(db: Session, token: str) -> LoginChallenge:
    payload = decode_login_challenge_token(token)
    challenge_jti = payload.get("jti")
    user_id_raw = payload.get("sub")

    if not isinstance(challenge_jti, str) or not challenge_jti:
        raise LoginChallengeError("登录挑战无效或已过期")
    if not isinstance(user_id_raw, str) or not user_id_raw.isdigit():
        raise LoginChallengeError("登录挑战无效或已过期")

    challenge = LoginChallengeDAO(db).get_by_jti(challenge_jti)
    if challenge is None or challenge.user_id != int(user_id_raw):
        raise LoginChallengeError("登录挑战无效或已过期")
    if challenge.consumed_at is not None:
        raise LoginChallengeError("登录挑战已失效，请重新登录")
    if _ensure_aware(challenge.expires_at) <= _utcnow():
        raise LoginChallengeError("登录挑战已过期，请重新登录")
    if challenge.attempt_count >= auth_config.two_factor_max_verify_attempts:
        raise LoginChallengeError("验证码错误次数过多，请重新登录")
    return challenge


def record_login_challenge_failure(
    db: Session, challenge: LoginChallenge
) -> LoginChallenge:
    return LoginChallengeDAO(db).increment_attempts(challenge)


def consume_login_challenge(db: Session, challenge: LoginChallenge) -> LoginChallenge:
    return LoginChallengeDAO(db).consume(challenge)

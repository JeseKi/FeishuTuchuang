# -*- coding: utf-8 -*-
"""OAuth core service."""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.config import auth_config
from src.server.auth.dao import UserDAO
from src.server.auth.models import User
from src.server.config import global_config
from src.server.oauth.config import oauth_config
from src.server.oauth.dao import OAuthAccountDAO, OAuthLoginTicketDAO
from src.server.oauth.models import OAuthLoginTicket
from src.server.oauth.schemas import GitHubUserInfo, GoogleUserInfo, OAuthProviderOut
from src.server.oauth.service.github import GITHUB_PROVIDER
from src.server.oauth.service.google import GOOGLE_PROVIDER

TOKEN_TYPE_OAUTH_STATE = "oauth_state"
PROVIDER_GITHUB = GITHUB_PROVIDER
PROVIDER_GOOGLE = GOOGLE_PROVIDER
OAUTH_USERNAME_ALPHABET = string.ascii_lowercase + string.digits + "_"


class OAuthError(Exception):
    """OAuth 业务异常。"""


def is_provider_enabled(provider: str) -> bool:
    return provider.upper() in global_config.oauth_list


def list_enabled_providers() -> list[OAuthProviderOut]:
    providers: list[OAuthProviderOut] = []
    if is_provider_enabled(PROVIDER_GITHUB):
        providers.append(OAuthProviderOut(provider="GITHUB", label="GitHub"))
    if is_provider_enabled(PROVIDER_GOOGLE):
        providers.append(OAuthProviderOut(provider="GOOGLE", label="Google"))
    return providers


def assert_provider_enabled(provider: str) -> None:
    if not is_provider_enabled(provider):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{provider} OAuth 未启用",
        )


def create_oauth_state(redirect_path: str | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=oauth_config.oauth_state_ttl_minutes
    )
    payload = {
        "type": TOKEN_TYPE_OAUTH_STATE,
        "nonce": secrets.token_urlsafe(16),
        "redirect_path": _normalize_redirect_path(redirect_path),
        "exp": expires_at,
    }
    return jwt.encode(
        payload, auth_config.jwt_secret_key, algorithm=auth_config.jwt_algorithm
    )


def decode_oauth_state(state: str) -> dict:
    try:
        payload = jwt.decode(
            state, auth_config.jwt_secret_key, algorithms=[auth_config.jwt_algorithm]
        )
    except JWTError as exc:
        raise OAuthError("OAuth state 无效或已过期") from exc
    if payload.get("type") != TOKEN_TYPE_OAUTH_STATE:
        raise OAuthError("OAuth state 类型无效")
    return payload


def resolve_github_user(db: Session, github_user: GitHubUserInfo) -> User:
    return _resolve_provider_user(
        db,
        provider=PROVIDER_GITHUB,
        provider_label="GitHub",
        provider_user_id=github_user.provider_user_id,
        username_candidate=github_user.login,
        provider_username=github_user.login,
        provider_email=github_user.email,
        provider_name=github_user.name,
        avatar_url=github_user.avatar_url,
    )


def resolve_google_user(db: Session, google_user: GoogleUserInfo) -> User:
    username_candidate = google_user.email.split("@", maxsplit=1)[0]
    return _resolve_provider_user(
        db,
        provider=PROVIDER_GOOGLE,
        provider_label="Google",
        provider_user_id=google_user.provider_user_id,
        username_candidate=username_candidate,
        provider_username=google_user.email,
        provider_email=google_user.email,
        provider_name=google_user.name,
        avatar_url=google_user.avatar_url,
    )


def _resolve_provider_user(
    db: Session,
    *,
    provider: str,
    provider_label: str,
    provider_user_id: str,
    username_candidate: str,
    provider_username: str | None,
    provider_email: str,
    provider_name: str | None,
    avatar_url: str | None,
) -> User:
    account_dao = OAuthAccountDAO(db)
    user_dao = UserDAO(db)

    account = account_dao.get_by_provider_user_id(
        provider, provider_user_id
    )
    if account is not None:
        user = user_dao.get_by_id(account.user_id)
        if user is None:
            raise OAuthError("OAuth 绑定用户不存在")
        account_dao.update_metadata(
            account,
            provider_username=provider_username,
            provider_email=provider_email,
            provider_name=provider_name,
            avatar_url=avatar_url,
        )
        return user

    user = user_dao.get_by_email(provider_email)
    if user is None:
        user = _create_oauth_user(
            db,
            provider=provider,
            username_candidate=username_candidate,
            email=provider_email,
            name=provider_name,
        )

    existing_provider_user = account_dao.get_by_provider_user(provider, user.id)
    if existing_provider_user is not None:
        raise OAuthError(f"该本地账号已绑定其他 {provider_label} 账号")

    try:
        account_dao.create(
            provider=provider,
            provider_user_id=provider_user_id,
            user_id=user.id,
            provider_username=provider_username,
            provider_email=provider_email,
            provider_name=provider_name,
            avatar_url=avatar_url,
        )
    except IntegrityError as exc:
        db.rollback()
        raise OAuthError(f"{provider_label} 账号绑定失败，请重试") from exc

    return user


def create_login_ticket(db: Session, provider: str, user: User) -> str:
    challenge_token = None
    if auth_service.is_two_factor_enabled(user):
        challenge_token = auth_service.begin_login_challenge(db, user)

    raw_ticket = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=oauth_config.oauth_ticket_ttl_minutes
    )
    OAuthLoginTicketDAO(db).create(
        ticket_hash=hash_ticket(raw_ticket),
        provider=provider,
        user_id=user.id,
        challenge_token=challenge_token,
        expires_at=expires_at,
    )
    return raw_ticket


def exchange_login_ticket(db: Session, raw_ticket: str) -> tuple[User, str | None]:
    ticket_dao = OAuthLoginTicketDAO(db)
    ticket = ticket_dao.get_by_hash(hash_ticket(raw_ticket))
    if ticket is None or not _is_ticket_active(ticket):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth 登录票据无效或已过期",
        )
    assert_provider_enabled(ticket.provider)

    user = UserDAO(db).get_by_id(ticket.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth 登录票据无效",
        )

    ticket_dao.consume(ticket)
    return user, ticket.challenge_token


def hash_ticket(raw_ticket: str) -> str:
    return hashlib.sha256(raw_ticket.encode("utf-8")).hexdigest()


def _create_oauth_user(
    db: Session,
    *,
    provider: str,
    username_candidate: str,
    email: str,
    name: str | None,
) -> User:
    username = _make_unique_username(db, username_candidate, provider.lower())
    user = User(
        username=username,
        email=email,
        name=name or username,
    )
    user.set_password(secrets.token_urlsafe(32))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_unique_username(db: Session, candidate: str, fallback_prefix: str) -> str:
    normalized = "".join(
        char.lower() if char.lower() in OAUTH_USERNAME_ALPHABET else "_"
        for char in candidate.strip()
    ).strip("_")
    if len(normalized) < 3:
        normalized = f"{fallback_prefix}_user"
    normalized = normalized[:50]

    user_dao = UserDAO(db)
    if user_dao.get_by_username(normalized) is None:
        return normalized

    base = normalized[:41]
    for _ in range(10):
        suffix = secrets.token_hex(4)
        username = f"{base}_{suffix}"[:50]
        if user_dao.get_by_username(username) is None:
            return username
    return f"{fallback_prefix}_{secrets.token_hex(8)}"[:50]


def _is_ticket_active(ticket: OAuthLoginTicket) -> bool:
    if ticket.consumed_at is not None:
        return False
    expires_at = ticket.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def _normalize_redirect_path(redirect_path: str | None) -> str:
    if not redirect_path or not redirect_path.startswith("/"):
        return "/"
    if redirect_path.startswith("//") or "\n" in redirect_path or "\r" in redirect_path:
        return "/"
    return redirect_path

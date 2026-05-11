# -*- coding: utf-8 -*-
"""OAuth routes."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.config import auth_config
from src.server.auth.models import User
from src.server.auth.schemas import LoginChallengeResponse, TokenResponse
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db
from src.server.config import global_config
from src.server.providers import (
    get_github_oauth_provider,
    get_google_oauth_provider,
)
from .schemas import OAuthProvidersResponse, OAuthTicketExchange
from .service import core
from .service.github import GITHUB_PROVIDER, GitHubOAuthError
from .service.google import GOOGLE_PROVIDER, GoogleOAuthError

router = APIRouter(prefix="/api/oauth", tags=["OAuth"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=auth_config.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=auth_config.refresh_cookie_secure,
        samesite=auth_config.refresh_cookie_samesite,  # type: ignore[arg-type]
        max_age=auth_config.refresh_token_ttl_days * 24 * 60 * 60,
        path="/api/auth",
    )


def _build_token_response(access_token: str, user: User) -> dict[str, str]:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "scope": auth_service.serialize_scopes(auth_service.get_user_scopes(user)),
    }


def _build_frontend_login_url(
    *,
    ticket: str | None = None,
    error: str | None = None,
    redirect_path: str | None = None,
) -> str:
    base_url = global_config.app_domain.strip() or ""
    target = f"{base_url}/login"
    params = {}
    if ticket:
        params["oauth_ticket"] = ticket
    if error:
        params["oauth_error"] = error
    if redirect_path and redirect_path.startswith("/") and not redirect_path.startswith("//"):
        params["oauth_redirect_path"] = redirect_path
    if not params:
        return target
    return f"{target}?{urlencode(params)}"


@router.get(
    "/providers",
    response_model=OAuthProvidersResponse,
    summary="获取已启用 OAuth 渠道",
)
async def list_providers():
    return OAuthProvidersResponse(providers=core.list_enabled_providers())


@router.get(
    "/github/authorize",
    summary="开始 GitHub OAuth 登录",
)
async def authorize_github(
    redirect_path: str | None = Query(default=None),
):
    core.assert_provider_enabled(GITHUB_PROVIDER)
    state = core.create_oauth_state(redirect_path)
    try:
        return RedirectResponse(get_github_oauth_provider().build_authorize_url(state))
    except GitHubOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/github/callback",
    summary="GitHub OAuth 回调",
)
async def github_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    core.assert_provider_enabled(GITHUB_PROVIDER)
    if error:
        return RedirectResponse(_build_frontend_login_url(error=error_description or error))
    if not code or not state:
        return RedirectResponse(_build_frontend_login_url(error="GitHub OAuth 参数缺失"))

    try:
        state_payload = core.decode_oauth_state(state)
    except core.OAuthError as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    try:
        github_user = await get_github_oauth_provider().fetch_user_info(code)
    except (GitHubOAuthError, Exception) as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    def _complete_callback() -> str:
        user = core.resolve_github_user(db, github_user)
        return core.create_login_ticket(db, GITHUB_PROVIDER, user)

    try:
        ticket = await run_in_thread(_complete_callback)
    except core.OAuthError as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    redirect_path = state_payload.get("redirect_path")
    return RedirectResponse(
        _build_frontend_login_url(
            ticket=ticket,
            redirect_path=redirect_path if isinstance(redirect_path, str) else None,
        )
    )


@router.get(
    "/google/authorize",
    summary="开始 Google OAuth 登录",
)
async def authorize_google(
    redirect_path: str | None = Query(default=None),
):
    core.assert_provider_enabled(GOOGLE_PROVIDER)
    state = core.create_oauth_state(redirect_path)
    try:
        return RedirectResponse(get_google_oauth_provider().build_authorize_url(state))
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/google/callback",
    summary="Google OAuth 回调",
)
async def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    core.assert_provider_enabled(GOOGLE_PROVIDER)
    if error:
        return RedirectResponse(_build_frontend_login_url(error=error_description or error))
    if not code or not state:
        return RedirectResponse(_build_frontend_login_url(error="Google OAuth 参数缺失"))

    try:
        state_payload = core.decode_oauth_state(state)
    except core.OAuthError as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    try:
        google_user = await get_google_oauth_provider().fetch_user_info(code)
    except (GoogleOAuthError, Exception) as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    def _complete_callback() -> str:
        user = core.resolve_google_user(db, google_user)
        return core.create_login_ticket(db, GOOGLE_PROVIDER, user)

    try:
        ticket = await run_in_thread(_complete_callback)
    except core.OAuthError as exc:
        return RedirectResponse(_build_frontend_login_url(error=str(exc)))

    redirect_path = state_payload.get("redirect_path")
    return RedirectResponse(
        _build_frontend_login_url(
            ticket=ticket,
            redirect_path=redirect_path if isinstance(redirect_path, str) else None,
        )
    )


@router.post(
    "/ticket",
    response_model=TokenResponse | LoginChallengeResponse,
    summary="交换 OAuth 登录票据",
    responses={
        200: {"description": "OAuth 登录成功或需要继续完成 2FA"},
        401: {"description": "票据无效、过期或已消费"},
    },
)
async def exchange_ticket(
    payload: OAuthTicketExchange,
    response: Response,
    db: Session = Depends(get_db),
):
    def _exchange():
        return core.exchange_login_ticket(db, payload.ticket)

    user, challenge_token = await run_in_thread(_exchange)
    if challenge_token:
        return LoginChallengeResponse(challenge_token=challenge_token)

    def _issue_tokens():
        return auth_service.issue_token_pair(db, user)

    access_token, refresh_token = await run_in_thread(_issue_tokens)
    _set_refresh_cookie(response, refresh_token)
    return _build_token_response(access_token, user)

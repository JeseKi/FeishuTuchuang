# -*- coding: utf-8 -*-
"""Google OAuth service."""

from __future__ import annotations

import httpx

from src.server.oauth.config import oauth_config
from src.server.oauth.schemas import GoogleUserInfo

GOOGLE_PROVIDER = "GOOGLE"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_ACCESS_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthError(Exception):
    """Google OAuth 异常。"""


def is_google_configured() -> bool:
    return bool(
        oauth_config.google_client_id.strip()
        and oauth_config.google_client_secret.strip()
        and oauth_config.google_redirect_uri.strip()
    )


def build_authorize_url(state: str) -> str:
    if not oauth_config.google_client_id.strip():
        raise GoogleOAuthError("Google OAuth Client ID 未配置")

    request = httpx.Request(
        "GET",
        GOOGLE_AUTHORIZE_URL,
        params={
            "client_id": oauth_config.google_client_id,
            "redirect_uri": oauth_config.google_redirect_uri,
            "response_type": "code",
            "scope": oauth_config.google_scope,
            "state": state,
            "include_granted_scopes": "true",
        },
    )
    return str(request.url)


async def fetch_user_info(code: str) -> GoogleUserInfo:
    if not is_google_configured():
        raise GoogleOAuthError("Google OAuth 未完整配置")

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            GOOGLE_ACCESS_TOKEN_URL,
            data={
                "client_id": oauth_config.google_client_id,
                "client_secret": oauth_config.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": oauth_config.google_redirect_uri,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            detail = token_data.get("error_description") or token_data.get("error")
            raise GoogleOAuthError(str(detail or "Google token 交换失败"))

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()

    user_data = user_resp.json()
    provider_user_id = user_data.get("sub")
    email = user_data.get("email")
    email_verified = user_data.get("email_verified")
    if not isinstance(provider_user_id, str) or not provider_user_id:
        raise GoogleOAuthError("Google 用户信息不完整")
    if not isinstance(email, str) or not email.strip():
        raise GoogleOAuthError("Google 未返回邮箱")
    if email_verified is not True:
        raise GoogleOAuthError("Google 未返回已验证邮箱")

    name = user_data.get("name")
    avatar_url = user_data.get("picture")
    return GoogleUserInfo(
        provider_user_id=provider_user_id,
        email=email.strip().lower(),
        name=name if isinstance(name, str) and name else None,
        avatar_url=avatar_url if isinstance(avatar_url, str) and avatar_url else None,
    )

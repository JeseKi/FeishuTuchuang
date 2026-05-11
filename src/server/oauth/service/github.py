# -*- coding: utf-8 -*-
"""GitHub OAuth service."""

from __future__ import annotations

import httpx

from src.server.oauth.config import oauth_config
from src.server.oauth.schemas import GitHubUserInfo

GITHUB_PROVIDER = "GITHUB"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class GitHubOAuthError(Exception):
    """GitHub OAuth 异常。"""


def is_github_configured() -> bool:
    return bool(
        oauth_config.github_client_id.strip()
        and oauth_config.github_client_secret.strip()
        and oauth_config.github_redirect_uri.strip()
    )


def build_authorize_url(state: str) -> str:
    if not oauth_config.github_client_id.strip():
        raise GitHubOAuthError("GitHub OAuth Client ID 未配置")

    request = httpx.Request(
        "GET",
        GITHUB_AUTHORIZE_URL,
        params={
            "client_id": oauth_config.github_client_id,
            "redirect_uri": oauth_config.github_redirect_uri,
            "scope": oauth_config.github_scope,
            "state": state,
            "allow_signup": "true",
        },
    )
    return str(request.url)


async def fetch_user_info(code: str) -> GitHubUserInfo:
    if not is_github_configured():
        raise GitHubOAuthError("GitHub OAuth 未完整配置")

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            GITHUB_ACCESS_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": oauth_config.github_client_id,
                "client_secret": oauth_config.github_client_secret,
                "code": code,
                "redirect_uri": oauth_config.github_redirect_uri,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            detail = token_data.get("error_description") or token_data.get("error")
            raise GitHubOAuthError(str(detail or "GitHub token 交换失败"))

        auth_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        user_resp = await client.get(GITHUB_USER_URL, headers=auth_headers)
        user_resp.raise_for_status()
        email_resp = await client.get(GITHUB_EMAILS_URL, headers=auth_headers)
        email_resp.raise_for_status()

    user_data = user_resp.json()
    emails_data = email_resp.json()
    email = _extract_verified_primary_email(emails_data)
    if email is None:
        raise GitHubOAuthError("GitHub 未返回已验证的主邮箱")

    provider_user_id = user_data.get("id")
    login = user_data.get("login")
    if provider_user_id is None or not isinstance(login, str) or not login:
        raise GitHubOAuthError("GitHub 用户信息不完整")

    name = user_data.get("name")
    avatar_url = user_data.get("avatar_url")
    return GitHubUserInfo(
        provider_user_id=str(provider_user_id),
        login=login,
        email=email.lower(),
        name=name if isinstance(name, str) and name else None,
        avatar_url=avatar_url if isinstance(avatar_url, str) and avatar_url else None,
    )


def _extract_verified_primary_email(emails_data: object) -> str | None:
    if not isinstance(emails_data, list):
        return None
    for item in emails_data:
        if not isinstance(item, dict):
            continue
        if item.get("primary") is True and item.get("verified") is True:
            email = item.get("email")
            if isinstance(email, str) and email.strip():
                return email.strip()
    return None


# -*- coding: utf-8 -*-
"""GitHub OAuth external provider implementations."""

from __future__ import annotations

from abc import abstractmethod

from src.server.oauth.schemas import GitHubUserInfo
from src.server.oauth.config import oauth_config
from src.server.oauth.service import github
from src.server.providers.base import ExternalProvider
from src.server.providers.constants import PROVIDER_GITHUB_OAUTH
from src.server.providers.runtime import get_provider_runtime_config


class GitHubOAuthProvider(ExternalProvider):
    key = PROVIDER_GITHUB_OAUTH
    label = "GitHub OAuth"
    kind = "oauth"

    @abstractmethod
    def build_authorize_url(self, state: str) -> str:
        """Build a GitHub authorize URL."""

    @abstractmethod
    async def fetch_user_info(self, code: str) -> GitHubUserInfo:
        """Exchange a callback code for GitHub user info."""


class RealGitHubOAuthProvider(GitHubOAuthProvider):
    implementation = "real"

    def is_configured(self) -> bool:
        return github.is_github_configured()

    def build_authorize_url(self, state: str) -> str:
        return github.build_authorize_url(state)

    async def fetch_user_info(self, code: str) -> GitHubUserInfo:
        return await github.fetch_user_info(code)


class MockGitHubOAuthProvider(GitHubOAuthProvider):
    implementation = "mock"

    def is_configured(self) -> bool:
        return bool(_base_url())

    def build_authorize_url(self, state: str) -> str:
        base_url = _base_url()
        request = github.httpx.Request(
            "GET",
            f"{base_url}/login/oauth/authorize",
            params={
                "client_id": _client_id(),
                "redirect_uri": _redirect_uri(),
                "scope": oauth_config.github_scope,
                "state": state,
                "allow_signup": "true",
            },
        )
        return str(request.url)

    async def fetch_user_info(self, code: str) -> GitHubUserInfo:
        base_url = _base_url()
        async with github.httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            token_resp = await client.post(
                f"{base_url}/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": _client_id(),
                    "client_secret": _client_secret(),
                    "code": code,
                    "redirect_uri": _redirect_uri(),
                },
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise github.GitHubOAuthError("GitHub mock token 交换失败")

            auth_headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            user_resp = await client.get(f"{base_url}/user", headers=auth_headers)
            user_resp.raise_for_status()
            email_resp = await client.get(f"{base_url}/user/emails", headers=auth_headers)
            email_resp.raise_for_status()

        user_data = user_resp.json()
        emails_data = email_resp.json()
        email = github._extract_verified_primary_email(emails_data)
        if email is None:
            raise github.GitHubOAuthError("GitHub mock 未返回已验证的主邮箱")
        provider_user_id = user_data.get("id")
        login = user_data.get("login")
        if provider_user_id is None or not isinstance(login, str) or not login:
            raise github.GitHubOAuthError("GitHub mock 用户信息不完整")
        name = user_data.get("name")
        avatar_url = user_data.get("avatar_url")
        return GitHubUserInfo(
            provider_user_id=str(provider_user_id),
            login=login,
            email=email.lower(),
            name=name if isinstance(name, str) and name else None,
            avatar_url=avatar_url if isinstance(avatar_url, str) and avatar_url else None,
        )


def _runtime_config() -> dict:
    return get_provider_runtime_config(PROVIDER_GITHUB_OAUTH)


def _base_url() -> str:
    return str(_runtime_config().get("base_url", "")).rstrip("/")


def _client_id() -> str:
    return str(_runtime_config().get("client_id") or oauth_config.github_client_id or "mock-github-client")


def _client_secret() -> str:
    return str(_runtime_config().get("client_secret") or oauth_config.github_client_secret or "mock-github-secret")


def _redirect_uri() -> str:
    return str(_runtime_config().get("redirect_uri") or oauth_config.github_redirect_uri)

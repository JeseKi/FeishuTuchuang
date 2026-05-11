# -*- coding: utf-8 -*-
"""Google OAuth external provider implementations."""

from __future__ import annotations

from abc import abstractmethod

from src.server.oauth.schemas import GoogleUserInfo
from src.server.oauth.config import oauth_config
from src.server.oauth.service import google
from src.server.providers.base import ExternalProvider
from src.server.providers.constants import PROVIDER_GOOGLE_OAUTH
from src.server.providers.runtime import get_provider_runtime_config


class GoogleOAuthProvider(ExternalProvider):
    key = PROVIDER_GOOGLE_OAUTH
    label = "Google OAuth"
    kind = "oauth"

    @abstractmethod
    def build_authorize_url(self, state: str) -> str:
        """Build a Google authorize URL."""

    @abstractmethod
    async def fetch_user_info(self, code: str) -> GoogleUserInfo:
        """Exchange a callback code for Google user info."""


class RealGoogleOAuthProvider(GoogleOAuthProvider):
    implementation = "real"

    def is_configured(self) -> bool:
        return google.is_google_configured()

    def build_authorize_url(self, state: str) -> str:
        return google.build_authorize_url(state)

    async def fetch_user_info(self, code: str) -> GoogleUserInfo:
        return await google.fetch_user_info(code)


class MockGoogleOAuthProvider(GoogleOAuthProvider):
    implementation = "mock"

    def is_configured(self) -> bool:
        return bool(_base_url())

    def build_authorize_url(self, state: str) -> str:
        base_url = _base_url()
        request = google.httpx.Request(
            "GET",
            f"{base_url}/o/oauth2/v2/auth",
            params={
                "client_id": _client_id(),
                "redirect_uri": _redirect_uri(),
                "response_type": "code",
                "scope": oauth_config.google_scope,
                "state": state,
                "include_granted_scopes": "true",
            },
        )
        return str(request.url)

    async def fetch_user_info(self, code: str) -> GoogleUserInfo:
        base_url = _base_url()
        async with google.httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            token_resp = await client.post(
                f"{base_url}/token",
                data={
                    "client_id": _client_id(),
                    "client_secret": _client_secret(),
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": _redirect_uri(),
                },
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise google.GoogleOAuthError("Google mock token 交换失败")

            user_resp = await client.get(
                f"{base_url}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()

        user_data = user_resp.json()
        provider_user_id = user_data.get("sub")
        email = user_data.get("email")
        email_verified = user_data.get("email_verified")
        if not isinstance(provider_user_id, str) or not provider_user_id:
            raise google.GoogleOAuthError("Google mock 用户信息不完整")
        if not isinstance(email, str) or not email.strip():
            raise google.GoogleOAuthError("Google mock 未返回邮箱")
        if email_verified is not True:
            raise google.GoogleOAuthError("Google mock 未返回已验证邮箱")
        name = user_data.get("name")
        avatar_url = user_data.get("picture")
        return GoogleUserInfo(
            provider_user_id=provider_user_id,
            email=email.strip().lower(),
            name=name if isinstance(name, str) and name else None,
            avatar_url=avatar_url if isinstance(avatar_url, str) and avatar_url else None,
        )


def _runtime_config() -> dict:
    return get_provider_runtime_config(PROVIDER_GOOGLE_OAUTH)


def _base_url() -> str:
    return str(_runtime_config().get("base_url", "")).rstrip("/")


def _client_id() -> str:
    return str(_runtime_config().get("client_id") or oauth_config.google_client_id or "mock-google-client")


def _client_secret() -> str:
    return str(_runtime_config().get("client_secret") or oauth_config.google_client_secret or "mock-google-secret")


def _redirect_uri() -> str:
    return str(_runtime_config().get("redirect_uri") or oauth_config.google_redirect_uri)

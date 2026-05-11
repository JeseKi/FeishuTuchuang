# -*- coding: utf-8 -*-
"""OAuth provider configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OAuthConfig(BaseSettings):
    """OAuth 配置。"""

    github_client_id: str = Field(default="", title="GitHub OAuth Client ID")
    github_client_secret: str = Field(default="", title="GitHub OAuth Client Secret")
    github_redirect_uri: str = Field(
        default="http://localhost:8000/api/oauth/github/callback",
        title="GitHub OAuth Callback URL",
    )
    github_scope: str = Field(
        default="read:user user:email",
        title="GitHub OAuth Scope",
    )
    google_client_id: str = Field(default="", title="Google OAuth Client ID")
    google_client_secret: str = Field(default="", title="Google OAuth Client Secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/oauth/google/callback",
        title="Google OAuth Callback URL",
    )
    google_scope: str = Field(
        default="openid email profile",
        title="Google OAuth Scope",
    )
    oauth_ticket_ttl_minutes: int = Field(default=5, title="OAuth 登录票据有效期")
    oauth_state_ttl_minutes: int = Field(default=10, title="OAuth state 有效期")

    model_config = SettingsConfigDict(
        env_file=None, env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


oauth_config = OAuthConfig()

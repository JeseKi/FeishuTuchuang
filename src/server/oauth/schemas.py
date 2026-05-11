# -*- coding: utf-8 -*-
"""OAuth schemas."""

from typing import Literal

from pydantic import BaseModel, Field


OAuthProviderName = Literal["GITHUB", "GOOGLE"]


class OAuthProviderOut(BaseModel):
    provider: OAuthProviderName
    label: str


class OAuthProvidersResponse(BaseModel):
    providers: list[OAuthProviderOut]


class OAuthTicketExchange(BaseModel):
    ticket: str = Field(..., min_length=32, max_length=256)


class GitHubUserInfo(BaseModel):
    provider_user_id: str
    login: str
    email: str
    name: str | None = None
    avatar_url: str | None = None


class GoogleUserInfo(BaseModel):
    provider_user_id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None

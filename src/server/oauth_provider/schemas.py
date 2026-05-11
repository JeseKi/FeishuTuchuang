# -*- coding: utf-8 -*-
"""OAuth Provider schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OAuthClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    redirect_uris: list[str] = Field(..., min_length=1)
    allowed_scopes: list[str] = Field(default_factory=list)
    is_active: bool = True
    require_pkce: bool = True

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, values: list[str]) -> list[str]:
        normalized = []
        for value in values:
            uri = value.strip()
            if not uri:
                continue
            if "\n" in uri or "\r" in uri:
                raise ValueError("redirect_uri 不合法")
            normalized.append(uri)
        if not normalized:
            raise ValueError("至少需要一个 redirect_uri")
        return list(dict.fromkeys(normalized))


class OAuthClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    redirect_uris: list[str] | None = None
    allowed_scopes: list[str] | None = None
    is_active: bool | None = None
    require_pkce: bool | None = None

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return OAuthClientCreate.validate_redirect_uris(values)


class OAuthClientOut(BaseModel):
    id: int
    client_id: str
    name: str
    redirect_uris: list[str]
    allowed_scopes: list[str]
    is_active: bool
    require_pkce: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OAuthClientSecretOut(OAuthClientOut):
    client_secret: str


class OAuthPermissionOut(BaseModel):
    scope: str
    title: str
    description: str


class OAuthAuthorizeMetadata(BaseModel):
    client_id: str
    client_name: str
    redirect_uri: str
    permissions: list[OAuthPermissionOut]
    state: str | None = None


class OAuthAuthorizeConfirm(BaseModel):
    response_type: str
    client_id: str
    redirect_uri: str
    scope: str = ""
    state: str | None = None
    code_challenge: str
    code_challenge_method: str = "S256"
    approve: bool = True


class OAuthAuthorizeResult(BaseModel):
    redirect_url: str


class OAuthDeviceAuthorizationResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


class OAuthDeviceAuthorizationMetadata(BaseModel):
    client_id: str
    client_name: str
    user_code: str
    permissions: list[OAuthPermissionOut]
    expires_at: datetime


class OAuthDeviceAuthorizationConfirm(BaseModel):
    user_code: str = Field(..., min_length=1)
    approve: bool = True


class OAuthDeviceAuthorizationResult(BaseModel):
    status: str


class OAuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class OAuthUserInfo(BaseModel):
    sub: str
    username: str
    email: str
    name: str | None = None

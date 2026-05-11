# -*- coding: utf-8 -*-
"""OAuth Provider routes."""

from __future__ import annotations

import base64
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_admin_writer, get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_PROFILE_READ
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from . import service
from .schemas import (
    OAuthAuthorizeConfirm,
    OAuthAuthorizeMetadata,
    OAuthAuthorizeResult,
    OAuthClientCreate,
    OAuthClientOut,
    OAuthClientSecretOut,
    OAuthClientUpdate,
    OAuthDeviceAuthorizationConfirm,
    OAuthDeviceAuthorizationMetadata,
    OAuthDeviceAuthorizationResponse,
    OAuthDeviceAuthorizationResult,
    OAuthTokenResponse,
    OAuthUserInfo,
)

router = APIRouter(prefix="/api/oauth-provider", tags=["OAuth Provider"])
bearer_scheme = HTTPBearer(auto_error=True)


@router.get("/clients", response_model=list[OAuthClientOut], summary="列出 OAuth Clients")
async def list_clients(
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.list_clients(db))


@router.post(
    "/clients",
    response_model=OAuthClientSecretOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建 OAuth Client",
)
async def create_client(
    payload: OAuthClientCreate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.create_client(
            db,
            name=payload.name,
            redirect_uris=payload.redirect_uris,
            allowed_scopes=payload.allowed_scopes,
            is_active=payload.is_active,
            require_pkce=payload.require_pkce,
        )
    )


@router.patch("/clients/{client_id}", response_model=OAuthClientOut, summary="更新 OAuth Client")
async def update_client(
    client_id: str,
    payload: OAuthClientUpdate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.update_client(db, client_id, payload.model_dump(exclude_unset=True))
    )


@router.delete(
    "/clients/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除 OAuth Client",
)
async def delete_client(
    client_id: str,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    await run_in_thread(lambda: service.delete_client(db, client_id))


@router.post(
    "/clients/{client_id}/secret",
    response_model=OAuthClientSecretOut,
    summary="重置 OAuth Client Secret",
)
async def reset_client_secret(
    client_id: str,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.reset_client_secret(db, client_id))


@router.get(
    "/authorize/metadata",
    response_model=OAuthAuthorizeMetadata,
    summary="获取 OAuth 授权请求元数据",
)
async def authorize_metadata(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(default=""),
    state: str | None = Query(default=None),
    code_challenge: str | None = Query(default=None),
    code_challenge_method: str | None = Query(default="S256"),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.get_authorize_metadata(
            db,
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    )


@router.post(
    "/authorize",
    response_model=OAuthAuthorizeResult,
    summary="确认 OAuth 授权并生成跳转地址",
)
async def authorize(
    payload: OAuthAuthorizeConfirm,
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
    db: Session = Depends(get_db),
):
    redirect_url = await run_in_thread(
        lambda: service.create_authorization_redirect(db, payload, current_user)
    )
    return {"redirect_url": redirect_url}


@router.post(
    "/device_authorization",
    response_model=OAuthDeviceAuthorizationResponse,
    summary="OAuth Device Authorization Endpoint",
)
async def device_authorization(request: Request, db: Session = Depends(get_db)):
    form = await _read_urlencoded_form(request)
    client_id, _ = _resolve_client_credentials(request, form)
    return await run_in_thread(
        lambda: service.create_device_authorization(
            db,
            client_id=client_id,
            scope=form.get("scope", ""),
        )
    )


@router.get(
    "/device/metadata",
    response_model=OAuthDeviceAuthorizationMetadata,
    summary="获取 OAuth Device 授权请求元数据",
)
async def device_authorization_metadata(
    user_code: str = Query(...),
    _: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.get_device_authorization_metadata(db, user_code=user_code)
    )


@router.post(
    "/device/authorize",
    response_model=OAuthDeviceAuthorizationResult,
    summary="确认 OAuth Device 授权",
)
async def device_authorize(
    payload: OAuthDeviceAuthorizationConfirm,
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_READ]),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.confirm_device_authorization(
            db,
            user_code=payload.user_code,
            approve=payload.approve,
            user=current_user,
        )
    )


@router.post("/token", response_model=OAuthTokenResponse, summary="OAuth Token Endpoint")
async def token(request: Request, db: Session = Depends(get_db)):
    form = await _read_urlencoded_form(request)
    client_id, client_secret = _resolve_client_credentials(request, form)
    grant_type = _get_required(form, "grant_type")

    if grant_type == "authorization_code":
        return await run_in_thread(
            lambda: service.exchange_authorization_code(
                db,
                client_id=client_id,
                client_secret=client_secret,
                code=_get_required(form, "code"),
                redirect_uri=_get_required(form, "redirect_uri"),
                code_verifier=form.get("code_verifier", ""),
            )
        )

    if grant_type == service.DEVICE_CODE_GRANT_TYPE:
        return await run_in_thread(
            lambda: service.exchange_device_code(
                db,
                client_id=client_id,
                client_secret=client_secret,
                device_code=_get_required(form, "device_code"),
            )
        )

    if grant_type == "refresh_token":
        return await run_in_thread(
            lambda: service.refresh_external_token(
                db,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=_get_required(form, "refresh_token"),
            )
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_grant_type")


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT, summary="撤销 OAuth Refresh Token")
async def revoke(request: Request, db: Session = Depends(get_db)):
    form = await _read_urlencoded_form(request)
    client_id, client_secret = _resolve_client_credentials(request, form)
    await run_in_thread(
        lambda: service.revoke_token(
            db,
            token=_get_required(form, "token"),
            client_id=client_id,
            client_secret=client_secret,
        )
    )


@router.get("/userinfo", response_model=OAuthUserInfo, summary="获取 OAuth 用户信息")
async def userinfo(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    return await run_in_thread(
        lambda: service.get_userinfo_from_token(db, credentials.credentials)
    )


async def _read_urlencoded_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items() if values}


def _resolve_client_credentials(
    request: Request, form: dict[str, str]
) -> tuple[str, str | None]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(auth_header.split(" ", maxsplit=1)[1]).decode("utf-8")
            client_id, client_secret = decoded.split(":", maxsplit=1)
            return client_id, client_secret
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_client")
    return _get_required(form, "client_id"), form.get("client_secret")


def _get_required(form: dict[str, str], key: str) -> str:
    value = form.get(key)
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"缺少参数: {key}")
    return value

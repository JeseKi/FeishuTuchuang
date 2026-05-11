# -*- coding: utf-8 -*-
"""飞书 Drive 用户 OAuth。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request, status

from src.server.config import global_config
from src.server.database import SessionLocal

from .config import image_host_config
from .dao import FeishuOAuthTokenDAO
from .models import ImageHostFeishuOAuthToken

_pending_states: set[str] = set()
_pending_states_lock = Lock()


def build_callback_url(request: Request) -> str:
    path = "/api/images/feishu/oauth/callback"
    if image_host_config.public_base_url:
        return f"{image_host_config.public_base_url.rstrip('/')}{path}"
    if global_config.app_domain:
        return f"{global_config.app_domain.rstrip('/')}{path}"
    return str(request.base_url).rstrip("/") + path


def create_authorize_url(request: Request) -> dict[str, str]:
    if not image_host_config.feishu_app_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="未配置 IMAGE_HOST_FEISHU_APP_ID",
        )

    state = secrets.token_urlsafe(24)
    with _pending_states_lock:
        _pending_states.add(state)

    callback_url = build_callback_url(request)
    query = {
        "app_id": image_host_config.feishu_app_id,
        "redirect_uri": callback_url,
        "state": state,
        "scope": image_host_config.feishu_oauth_scope,
    }
    authorize_url = (
        f"{image_host_config.feishu_api_base_url.rstrip('/')}/authen/v1/index?"
        f"{urlencode(query)}"
    )
    return {
        "authorize_url": authorize_url,
        "callback_url": callback_url,
        "state": state,
    }


async def handle_callback(code: str, state: str | None) -> None:
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 state")
    with _pending_states_lock:
        if state not in _pending_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或已过期的 state",
            )
        _pending_states.remove(state)

    token_payload = await _exchange_code_for_token(code)
    _save_token_payload(token_payload)


def get_oauth_status() -> dict:
    db = SessionLocal()
    try:
        token = FeishuOAuthTokenDAO(db).get()
        if token is None:
            return {"connected": False}
        return {
            "connected": True,
            "expires_at": token.expires_at,
            "refresh_expires_at": token.refresh_expires_at,
            "open_id": token.open_id,
            "union_id": token.union_id,
            "user_id": token.user_id,
            "connected_by_user_id": token.connected_by_user_id,
        }
    finally:
        db.close()


async def get_valid_user_access_token() -> str:
    db = SessionLocal()
    try:
        token = FeishuOAuthTokenDAO(db).get()
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="尚未连接飞书 Drive，请先完成飞书用户授权",
            )

        expires_at = _as_aware_datetime(token.expires_at)
        if expires_at > datetime.now(timezone.utc) + timedelta(seconds=60):
            return token.access_token

        refresh_token = token.refresh_token
    finally:
        db.close()

    token_payload = await _refresh_user_token(refresh_token)
    saved = _save_token_payload(token_payload)
    return saved.access_token


async def refresh_oauth_token_if_needed() -> bool:
    db = SessionLocal()
    try:
        token = FeishuOAuthTokenDAO(db).get()
        if token is None:
            return False
        expires_at = _as_aware_datetime(token.expires_at)
        refresh_token = token.refresh_token
    finally:
        db.close()

    refresh_before = timedelta(
        seconds=image_host_config.feishu_oauth_refresh_before_expiry_seconds
    )
    if expires_at > datetime.now(timezone.utc) + refresh_before:
        return False

    token_payload = await _refresh_user_token(refresh_token)
    _save_token_payload(token_payload)
    return True


async def _get_app_access_token() -> str:
    if not image_host_config.feishu_app_id or not image_host_config.feishu_app_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="未配置 IMAGE_HOST_FEISHU_APP_ID/IMAGE_HOST_FEISHU_APP_SECRET",
        )

    url = f"{image_host_config.feishu_api_base_url.rstrip('/')}/auth/v3/app_access_token/internal"
    body = {
        "app_id": image_host_config.feishu_app_id,
        "app_secret": image_host_config.feishu_app_secret,
    }
    async with httpx.AsyncClient(timeout=15, trust_env=True) as client:
        response = await client.post(url, json=body)
    payload = _json_or_error(response, "获取飞书 app_access_token 失败")
    app_access_token = payload.get("app_access_token")
    if not app_access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="飞书响应缺少 app_access_token",
        )
    return str(app_access_token)


async def _exchange_code_for_token(code: str) -> dict:
    app_access_token = await _get_app_access_token()
    url = f"{image_host_config.feishu_api_base_url.rstrip('/')}/authen/v1/oidc/access_token"
    headers = {"Authorization": f"Bearer {app_access_token}"}
    body = {
        "grant_type": "authorization_code",
        "code": code,
    }
    async with httpx.AsyncClient(timeout=30, trust_env=True) as client:
        response = await client.post(url, json=body, headers=headers)
    payload = _json_or_error(response, "飞书 OAuth 授权码换 token 失败")
    return dict(payload.get("data") or {})


async def _refresh_user_token(refresh_token: str) -> dict:
    app_access_token = await _get_app_access_token()
    url = f"{image_host_config.feishu_api_base_url.rstrip('/')}/authen/v1/oidc/refresh_access_token"
    headers = {"Authorization": f"Bearer {app_access_token}"}
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient(timeout=30, trust_env=True) as client:
        response = await client.post(url, json=body, headers=headers)
    payload = _json_or_error(response, "刷新飞书 user_access_token 失败")
    return dict(payload.get("data") or {})


def _save_token_payload(payload: dict) -> ImageHostFeishuOAuthToken:
    access_token = str(
        payload.get("access_token") or payload.get("user_access_token") or ""
    )
    refresh_token = str(payload.get("refresh_token") or "")
    if not access_token or not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="飞书 OAuth 响应缺少 access_token 或 refresh_token",
        )

    now = datetime.now(timezone.utc)
    expires_in = int(payload.get("expires_in") or payload.get("expire") or 7200)
    refresh_expires_in = payload.get("refresh_expires_in")
    refresh_expires_at = None
    if refresh_expires_in is not None:
        refresh_expires_at = now + timedelta(seconds=int(refresh_expires_in))

    db = SessionLocal()
    try:
        return FeishuOAuthTokenDAO(db).upsert(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + timedelta(seconds=expires_in),
            refresh_expires_at=refresh_expires_at,
            open_id=payload.get("open_id"),
            union_id=payload.get("union_id"),
            user_id=payload.get("user_id"),
        )
    finally:
        db.close()


def _json_or_error(response: httpx.Response, fallback_detail: str) -> dict:
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{fallback_detail}：HTTP {response.status_code}",
        )
    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{fallback_detail}：响应不是 JSON",
        )
    if payload.get("code") not in (0, None):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{fallback_detail}：{payload.get('msg') or payload.get('code')}",
        )
    return payload


def _as_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value

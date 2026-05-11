# -*- coding: utf-8 -*-
"""Development-only provider runtime configuration routes."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from src.server.auth.config import auth_config
from src.server.config import global_config
from .constants import ALL_PROVIDER_KEYS, PROVIDER_TURNSTILE
from .runtime import get_provider_runtime_config, update_provider_runtime_configs

router = APIRouter(prefix="/api/dev/providers", tags=["Dev Providers"])


class ProviderRuntimeConfigRequest(BaseModel):
    providers: dict[str, dict[str, Any]] = Field(default_factory=dict)


@router.post("/runtime-config", summary="更新外部 provider runtime 配置")
async def update_runtime_config(payload: ProviderRuntimeConfigRequest):
    if global_config.app_env != "dev":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev provider config route is only available in dev",
        )

    unknown = sorted(set(payload.providers) - set(ALL_PROVIDER_KEYS))
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider keys: {', '.join(unknown)}",
        )

    return {"providers": update_provider_runtime_configs(payload.providers)}


@router.get("/frontend-config", summary="获取前端 dev provider runtime 配置")
async def get_frontend_config():
    if global_config.app_env != "dev":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev provider config route is only available in dev",
        )

    turnstile_config = get_provider_runtime_config(PROVIDER_TURNSTILE)
    has_turnstile_mock = bool(str(turnstile_config.get("base_url", "")).strip())
    return {
        "turnstile": {
            "enabled": auth_config.turnstile_enabled,
            "site_key": str(turnstile_config.get("site_key") or "mock-site-key")
            if has_turnstile_mock
            else "",
            "script_url": "/api/dev/providers/turnstile/api.js"
            if has_turnstile_mock
            else "",
        }
    }


@router.get("/turnstile/api.js", summary="代理 Turnstile mock frontend script")
async def get_turnstile_mock_script():
    if global_config.app_env != "dev":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev provider config route is only available in dev",
        )

    turnstile_config = get_provider_runtime_config(PROVIDER_TURNSTILE)
    base_url = str(turnstile_config.get("base_url", "")).rstrip("/")
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Turnstile mock service is not registered",
        )

    async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
        response = await client.get(f"{base_url}/turnstile/v0/api.js")
        response.raise_for_status()

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/javascript"),
    )

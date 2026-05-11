# -*- coding: utf-8 -*-
"""Cloudflare Turnstile 人机校验工具。"""

from __future__ import annotations

from fastapi import Request


async def verify_turnstile_token(
    request: Request,
    token: str | None,
    *,
    action: str | None = None,
) -> None:
    """校验 Cloudflare Turnstile token。

    仅当 `auth_config.turnstile_enabled` 为真时执行远端校验。
    """
    from src.server.providers import get_turnstile_provider

    await get_turnstile_provider().verify_token(
        request=request,
        token=token,
        action=action,
    )

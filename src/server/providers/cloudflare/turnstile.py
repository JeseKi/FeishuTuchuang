# -*- coding: utf-8 -*-
"""Cloudflare Turnstile provider implementations."""

from __future__ import annotations

import json
from abc import abstractmethod
from json import JSONDecodeError
from typing import Any

import httpx
from fastapi import HTTPException, Request, status
from loguru import logger

from src.server.auth.config import auth_config
from src.server.providers.base import ExternalProvider
from src.server.providers.constants import PROVIDER_TURNSTILE
from src.server.providers.runtime import get_provider_runtime_config

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileProvider(ExternalProvider):
    key = PROVIDER_TURNSTILE
    label = "Cloudflare Turnstile"
    kind = "captcha"

    @abstractmethod
    async def verify_token(
        self,
        request: Request,
        token: str | None,
        *,
        action: str | None = None,
    ) -> None:
        """Verify a Turnstile token."""


class MockTurnstileProvider(TurnstileProvider):
    implementation = "mock"

    def is_configured(self) -> bool:
        return bool(_siteverify_url())

    async def verify_token(
        self,
        request: Request,
        token: str | None,
        *,
        action: str | None = None,
    ) -> None:
        if not auth_config.turnstile_enabled:
            return
        await _verify_with_siteverify(
            siteverify_url=_siteverify_url(),
            secret_key=_secret_key(),
            timeout_seconds=max(1, auth_config.turnstile_verify_timeout_seconds),
            request=request,
            token=token,
            action=action,
        )


class RealTurnstileProvider(TurnstileProvider):
    implementation = "real"

    def is_configured(self) -> bool:
        return bool(auth_config.turnstile_secret_key.strip())

    async def verify_token(
        self,
        request: Request,
        token: str | None,
        *,
        action: str | None = None,
    ) -> None:
        if not auth_config.turnstile_enabled:
            return

        if not auth_config.turnstile_secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务未完成 Turnstile 配置，请联系管理员。",
            )

        if not token or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请完成 Cloudflare 人机校验。",
            )

        await _verify_with_siteverify(
            siteverify_url=TURNSTILE_VERIFY_URL,
            secret_key=auth_config.turnstile_secret_key.strip(),
            timeout_seconds=max(1, auth_config.turnstile_verify_timeout_seconds),
            request=request,
            token=token,
            action=action,
        )


async def _verify_with_siteverify(
    *,
    siteverify_url: str,
    secret_key: str,
    timeout_seconds: int,
    request: Request,
    token: str | None,
    action: str | None,
) -> None:
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请完成 Cloudflare 人机校验。",
        )

    payload = {"secret": secret_key, "response": token}
    remote_ip = _extract_remote_ip(request)
    if remote_ip:
        payload["remoteip"] = remote_ip

    response: httpx.Response | None = None
    response_text: str | None = None
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=False) as client:
            response = await client.post(siteverify_url, data=payload)
            response.raise_for_status()
            response_text = response.text
            verify_payload = json.loads(response_text)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="人机校验服务暂时不可用，请稍后重试。",
        ) from exc
    except JSONDecodeError as exc:
        logger.warning(
            "Turnstile 响应解析失败 status={status}, body={body}",
            status=response.status_code if response is not None else None,
            body=response_text[:512] if response_text else "<empty or unavailable>",
        )
        logger.error("Turnstile 验证失败：无法解析响应，已中止验证流程。")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Turnstile 响应解析失败。",
        ) from exc

    if response is None:
        logger.error("Turnstile 验证失败：未获得响应对象，已中止验证流程。")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Turnstile 验证失败，请稍后重试。",
        )

    _assert_verify_payload(response, response_text, verify_payload)
    if not verify_payload.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"人机校验失败：{_format_errors(verify_payload)}",
        )

    if action is not None:
        verify_action = verify_payload.get("action")
        if verify_action and verify_action != action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="人机校验 action 不匹配。",
            )


def _runtime_config() -> dict:
    return get_provider_runtime_config(PROVIDER_TURNSTILE)


def _siteverify_url() -> str:
    configured = str(_runtime_config().get("siteverify_url", "")).strip()
    if configured:
        return configured
    base_url = str(_runtime_config().get("base_url", "")).rstrip("/")
    return f"{base_url}/turnstile/v0/siteverify" if base_url else ""


def _secret_key() -> str:
    return str(_runtime_config().get("secret_key") or "mock-turnstile-secret")


def _extract_remote_ip(request: Request) -> str | None:
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    return request.client.host if request.client else None


def _format_errors(payload: dict[str, Any]) -> str:
    raw_errors = payload.get("error-codes", [])
    if isinstance(raw_errors, list):
        errors = [str(item) for item in raw_errors if item]
        if errors:
            return ", ".join(errors)
    return "验证失败"


def _assert_verify_payload(
    response: httpx.Response,
    response_text: str | None,
    verify_payload: object,
) -> None:
    if verify_payload is None:
        logger.warning(
            "Turnstile 响应异常，解析后为 None。status={status}, body={body}",
            status=response.status_code,
            body=response_text[:512] if response_text else "<empty or unavailable>",
        )
        logger.error("Turnstile 验证失败：响应内容异常。")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Turnstile 响应异常。",
        )

    if not isinstance(verify_payload, dict):
        logger.warning(
            "Turnstile 响应格式异常，原始内容：{}",
            response_text[:512] if response_text else "<empty or unavailable>",
        )
        logger.error("Turnstile 验证失败：响应不是 JSON 对象。")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Turnstile 响应格式异常。",
        )

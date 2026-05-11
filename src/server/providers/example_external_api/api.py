# -*- coding: utf-8 -*-
"""Example external API provider implementations."""

from __future__ import annotations

from abc import abstractmethod

import httpx
from pydantic import BaseModel, Field

from src.server.config import global_config
from src.server.providers.base import ExternalProvider
from src.server.providers.constants import PROVIDER_EXAMPLE_EXTERNAL_API
from src.server.providers.runtime import get_provider_runtime_config


class ExampleExternalStatus(BaseModel):
    provider: str = Field(..., description="Provider implementation")
    status: str = Field(..., description="External API status")
    message: str | None = Field(default=None, description="Optional detail")


class ExampleExternalApiProvider(ExternalProvider):
    key = PROVIDER_EXAMPLE_EXTERNAL_API
    label = "Example External API"
    kind = "api"

    @abstractmethod
    async def fetch_status(self) -> ExampleExternalStatus:
        """Fetch status from an external API."""


class RealExampleExternalApiProvider(ExampleExternalApiProvider):
    implementation = "real"

    def is_configured(self) -> bool:
        return bool(global_config.example_external_api_base_url.strip())

    async def fetch_status(self) -> ExampleExternalStatus:
        if not self.is_configured():
            return ExampleExternalStatus(
                provider=self.implementation,
                status="not_configured",
                message="EXAMPLE_EXTERNAL_API_BASE_URL is not configured",
            )

        base_url = global_config.example_external_api_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            response = await client.get(f"{base_url}/status")
            response.raise_for_status()
            payload = response.json()

        status = payload.get("status") if isinstance(payload, dict) else None
        message = payload.get("message") if isinstance(payload, dict) else None
        return ExampleExternalStatus(
            provider=self.implementation,
            status=status if isinstance(status, str) and status else "ok",
            message=message if isinstance(message, str) and message else None,
        )


class MockExampleExternalApiProvider(ExampleExternalApiProvider):
    implementation = "mock"

    def is_configured(self) -> bool:
        return bool(_base_url())

    async def fetch_status(self) -> ExampleExternalStatus:
        base_url = _base_url()
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            response = await client.get(f"{base_url}/status")
            response.raise_for_status()
            payload = response.json()

        status = payload.get("status") if isinstance(payload, dict) else None
        message = payload.get("message") if isinstance(payload, dict) else None
        return ExampleExternalStatus(
            provider=self.implementation,
            status=status if isinstance(status, str) and status else "ok",
            message=message if isinstance(message, str) and message else None,
        )


def _base_url() -> str:
    configured = get_provider_runtime_config(PROVIDER_EXAMPLE_EXTERNAL_API).get("base_url")
    if configured:
        return str(configured).rstrip("/")
    return global_config.example_external_api_base_url.rstrip("/")

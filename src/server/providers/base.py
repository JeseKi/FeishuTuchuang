# -*- coding: utf-8 -*-
"""Base contracts for external providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

ProviderImplementation = Literal["real", "mock"]


@dataclass(frozen=True)
class ProviderHealth:
    """Lightweight provider health result."""

    ok: bool
    detail: str | None = None


class ExternalProvider(ABC):
    """Base class for replaceable third-party service providers."""

    key: str
    label: str
    kind: str
    implementation: ProviderImplementation

    @property
    def is_mock(self) -> bool:
        return self.implementation == "mock"

    @abstractmethod
    def is_configured(self) -> bool:
        """Return whether this provider has enough config to be used."""

    def health_check(self) -> ProviderHealth:
        if self.is_configured():
            return ProviderHealth(ok=True)
        return ProviderHealth(ok=False, detail="provider is not configured")

# -*- coding: utf-8 -*-
"""In-memory runtime configuration for external providers."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any

_runtime_configs: dict[str, dict[str, Any]] = {}
_lock = RLock()


def update_provider_runtime_config(
    provider_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Replace a provider's runtime config and return the stored value."""

    with _lock:
        _runtime_configs[provider_key] = dict(config)
        return deepcopy(_runtime_configs[provider_key])


def update_provider_runtime_configs(
    configs: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Replace multiple provider runtime configs."""

    updated: dict[str, dict[str, Any]] = {}
    with _lock:
        for provider_key, config in configs.items():
            _runtime_configs[provider_key] = dict(config)
            updated[provider_key] = deepcopy(_runtime_configs[provider_key])
    return updated


def get_provider_runtime_config(provider_key: str) -> dict[str, Any]:
    """Return a copy of a provider's runtime config."""

    with _lock:
        return deepcopy(_runtime_configs.get(provider_key, {}))


def clear_provider_runtime_configs() -> None:
    """Clear all runtime configs. Intended for tests."""

    with _lock:
        _runtime_configs.clear()

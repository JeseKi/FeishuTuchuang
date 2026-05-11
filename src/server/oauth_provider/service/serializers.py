# -*- coding: utf-8 -*-
"""OAuth Provider serialization helpers."""

import json

from src.server.auth import service as auth_service

from ..models import OAuthClient


def dump_json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def load_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def client_to_out(client: OAuthClient) -> dict:
    return {
        "id": client.id,
        "client_id": client.client_id,
        "name": client.name,
        "redirect_uris": load_json_list(client.redirect_uris),
        "allowed_scopes": list(auth_service.normalize_scopes(client.allowed_scopes)),
        "is_active": client.is_active,
        "require_pkce": client.require_pkce,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
    }


def permission_to_out(scope: str) -> dict[str, str]:
    definition = auth_service.get_scope_definition(scope)
    return {
        "scope": scope,
        "title": definition.title,
        "description": definition.description,
    }

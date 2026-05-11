# -*- coding: utf-8 -*-
"""OAuth Provider client management service."""

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth import service as auth_service

from ..dao import OAuthClientDAO
from ..models import OAuthClient
from .crypto import hash_secret
from .serializers import client_to_out, dump_json_list


def list_clients(db: Session) -> list[dict]:
    return [client_to_out(client) for client in OAuthClientDAO(db).list_all()]


def create_client(
    db: Session,
    *,
    name: str,
    redirect_uris: list[str],
    allowed_scopes: list[str],
    is_active: bool,
    require_pkce: bool,
) -> dict:
    client_id = _generate_unique_client_id(db)
    client_secret = f"os_{secrets.token_urlsafe(32)}"
    client = OAuthClient(
        client_id=client_id,
        client_secret_hash=hash_secret(client_secret),
        name=name.strip(),
        redirect_uris=dump_json_list(redirect_uris),
        allowed_scopes=auth_service.serialize_scopes(allowed_scopes),
        is_active=is_active,
        require_pkce=require_pkce,
    )
    created = OAuthClientDAO(db).create(client)
    return {**client_to_out(created), "client_secret": client_secret}


def update_client(db: Session, client_id: str, fields: dict) -> dict:
    dao = OAuthClientDAO(db)
    client = dao.get_by_client_id(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth Client 不存在")

    update_fields: dict[str, object] = {}
    if "name" in fields and fields["name"] is not None:
        update_fields["name"] = fields["name"].strip()
    if "redirect_uris" in fields and fields["redirect_uris"] is not None:
        update_fields["redirect_uris"] = dump_json_list(fields["redirect_uris"])
    if "allowed_scopes" in fields and fields["allowed_scopes"] is not None:
        update_fields["allowed_scopes"] = auth_service.serialize_scopes(fields["allowed_scopes"])
    if "is_active" in fields and fields["is_active"] is not None:
        update_fields["is_active"] = bool(fields["is_active"])
    if "require_pkce" in fields and fields["require_pkce"] is not None:
        update_fields["require_pkce"] = bool(fields["require_pkce"])
    if update_fields:
        client = dao.update(client, **update_fields)
    return client_to_out(client)


def delete_client(db: Session, client_id: str) -> None:
    dao = OAuthClientDAO(db)
    client = dao.get_by_client_id(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth Client 不存在")
    dao.delete(client)


def reset_client_secret(db: Session, client_id: str) -> dict:
    dao = OAuthClientDAO(db)
    client = dao.get_by_client_id(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth Client 不存在")
    client_secret = f"os_{secrets.token_urlsafe(32)}"
    client = dao.update(client, client_secret_hash=hash_secret(client_secret))
    return {**client_to_out(client), "client_secret": client_secret}


def _generate_unique_client_id(db: Session) -> str:
    dao = OAuthClientDAO(db)
    for _ in range(10):
        client_id = f"oc_{secrets.token_urlsafe(18)}"
        if dao.get_by_client_id(client_id) is None:
            return client_id
    return f"oc_{secrets.token_hex(24)}"

# -*- coding: utf-8 -*-
"""API Key 管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_PROFILE_WRITE
from src.server.database import get_db

from . import service
from .schemas import ApiKeyCreate, ApiKeyCreateOut, ApiKeyOut

router = APIRouter(prefix="/api/auth/api-keys", tags=["API Key"])


@router.get(
    "",
    response_model=list[ApiKeyOut],
    summary="列出当前用户 API Key",
)
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    return [
        service.to_output(api_key)
        for api_key in service.list_api_keys(db, current_user=current_user)
    ]


@router.post(
    "",
    response_model=ApiKeyCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建当前用户 API Key",
    description="API Key 只在创建时返回明文，请立即保存。",
)
async def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    api_key, raw_key = service.create_api_key(
        db,
        current_user=current_user,
        payload=payload,
    )
    return service.to_create_output(api_key, raw_key)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="撤销当前用户 API Key",
)
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[SCOPE_PROFILE_WRITE]),
):
    service.revoke_api_key(db, current_user=current_user, key_id=key_id)

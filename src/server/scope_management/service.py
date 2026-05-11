# -*- coding: utf-8 -*-
"""
scope 分类管理服务
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.service.scopes import (
    SCOPE_DEFINITIONS,
    SCOPE_ADMIN_USERS_READ,
    SCOPE_ADMIN_USERS_WRITE,
    SCOPE_PROFILE_EMAIL_WRITE,
    SCOPE_PROFILE_PASSWORD_WRITE,
)

from .dao import ManagedScopeDAO
from .models import ManagedScope
from .schemas import ScopeCategory

LEGACY_DEFAULT_SCOPE_CATEGORIES: dict[str, ScopeCategory] = {
    SCOPE_PROFILE_EMAIL_WRITE: ScopeCategory.SENSITIVE,
    SCOPE_PROFILE_PASSWORD_WRITE: ScopeCategory.SENSITIVE,
    SCOPE_ADMIN_USERS_READ: ScopeCategory.SENSITIVE,
    SCOPE_ADMIN_USERS_WRITE: ScopeCategory.SENSITIVE,
}

DEFAULT_SCOPE_CATEGORIES: dict[str, ScopeCategory] = {
    SCOPE_PROFILE_EMAIL_WRITE: ScopeCategory.SENSITIVE,
    SCOPE_PROFILE_PASSWORD_WRITE: ScopeCategory.DANGEROUS,
    SCOPE_ADMIN_USERS_READ: ScopeCategory.SENSITIVE,
    SCOPE_ADMIN_USERS_WRITE: ScopeCategory.DANGEROUS,
}


def get_default_scope_category(scope: str) -> ScopeCategory:
    return DEFAULT_SCOPE_CATEGORIES.get(scope, ScopeCategory.NORMAL)


def get_scope_category(db: Session, scope: str) -> ScopeCategory:
    managed_scope = ManagedScopeDAO(db).get_by_scope(scope)
    if managed_scope is not None:
        return managed_scope.category
    return get_default_scope_category(scope)


def has_dangerous_scope(db: Session, scopes: list[str] | tuple[str, ...]) -> bool:
    return any(
        get_scope_category(db, scope) == ScopeCategory.DANGEROUS for scope in scopes
    )


def sync_known_scopes(db: Session) -> list[ManagedScope]:
    dao = ManagedScopeDAO(db)
    existing_scopes = {item.scope: item for item in dao.list_all()}

    for definition in SCOPE_DEFINITIONS:
        scope = definition.scope
        description = definition.description
        existing = existing_scopes.get(scope)
        if existing is None:
            dao.create(scope, description, get_default_scope_category(scope))
            continue

        update_fields: dict[str, object] = {}
        if existing.description != description:
            update_fields["description"] = description

        legacy_default = LEGACY_DEFAULT_SCOPE_CATEGORIES.get(scope, ScopeCategory.NORMAL)
        desired_default = get_default_scope_category(scope)
        if existing.category == legacy_default and desired_default != legacy_default:
            update_fields["category"] = desired_default

        if update_fields:
            dao.update(existing, **update_fields)

    return dao.list_all()


def list_scopes(db: Session) -> list[ManagedScope]:
    return sync_known_scopes(db)


def update_scope_category(
    db: Session, scope: str, category: ScopeCategory
) -> ManagedScope:
    dao = ManagedScopeDAO(db)
    sync_known_scopes(db)

    managed_scope = dao.get_by_scope(scope)
    if managed_scope is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scope 不存在")

    return dao.update(managed_scope, category=category)

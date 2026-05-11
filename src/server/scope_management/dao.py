# -*- coding: utf-8 -*-
"""
scope 分类管理 DAO
"""

from __future__ import annotations

from sqlalchemy.orm import Session, object_session

from src.server.dao.dao_base import BaseDAO

from .models import ManagedScope
from .schemas import ScopeCategory


class ManagedScopeDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def list_all(self) -> list[ManagedScope]:
        return (
            self.db_session.query(ManagedScope)
            .order_by(ManagedScope.scope.asc())
            .all()
        )

    def get_by_scope(self, scope: str) -> ManagedScope | None:
        return (
            self.db_session.query(ManagedScope)
            .filter(ManagedScope.scope == scope)
            .first()
        )

    def create(
        self, scope: str, description: str, category: ScopeCategory
    ) -> ManagedScope:
        managed_scope = ManagedScope(
            scope=scope,
            description=description,
            category=category,
        )
        self.db_session.add(managed_scope)
        self.db_session.commit()
        self.db_session.refresh(managed_scope)
        return managed_scope

    def update(self, managed_scope: ManagedScope, **fields) -> ManagedScope:
        target = managed_scope
        if object_session(managed_scope) is not self.db_session:
            if managed_scope.id is None:
                raise ValueError("scope 不存在")
            fetched_scope = self.get_by_scope(managed_scope.scope)
            if fetched_scope is None:
                raise ValueError("scope 不存在")
            target = fetched_scope

        for key, value in fields.items():
            setattr(target, key, value)

        self.db_session.commit()
        self.db_session.refresh(target)
        return target


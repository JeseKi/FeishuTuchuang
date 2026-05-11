# -*- coding: utf-8 -*-
"""
scope 分类管理模型
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.server.database import Base

from .schemas import ScopeCategory


class ManagedScope(Base):
    __tablename__ = "managed_scopes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ScopeCategory] = mapped_column(
        SQLEnum(ScopeCategory), nullable=False, default=ScopeCategory.NORMAL
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def title(self) -> str:
        from src.server.auth.service.scopes import get_scope_title

        return get_scope_title(self.scope)

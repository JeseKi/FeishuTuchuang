# -*- coding: utf-8 -*-
"""
scope 分类管理 Pydantic 模型
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ScopeCategory(str, Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    DANGEROUS = "dangerous"


class ManagedScopeOut(BaseModel):
    id: int
    scope: str
    title: str
    description: str
    category: ScopeCategory
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManagedScopeUpdate(BaseModel):
    category: ScopeCategory

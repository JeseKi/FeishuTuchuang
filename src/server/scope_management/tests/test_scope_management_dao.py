# -*- coding: utf-8 -*-
"""
scope 分类管理 DAO 测试
"""

from sqlalchemy.orm import Session

from src.server.scope_management.dao import ManagedScopeDAO
from src.server.scope_management.schemas import ScopeCategory


def test_managed_scope_dao_create_and_get(test_db_session: Session):
    dao = ManagedScopeDAO(test_db_session)

    created = dao.create("profile:read", "读取当前用户资料", ScopeCategory.NORMAL)

    assert created.id is not None
    assert created.scope == "profile:read"
    assert created.category == ScopeCategory.NORMAL

    fetched = dao.get_by_scope("profile:read")
    assert fetched is not None
    assert fetched.id == created.id


def test_managed_scope_dao_update(test_db_session: Session):
    dao = ManagedScopeDAO(test_db_session)
    created = dao.create("profile:password:write", "修改当前用户密码", ScopeCategory.NORMAL)

    updated = dao.update(created, category=ScopeCategory.SENSITIVE)

    assert updated.category == ScopeCategory.SENSITIVE


# -*- coding: utf-8 -*-
"""
scope 分类管理服务测试
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.server.auth.service.scopes import OAUTH2_SCOPES
from src.server.scope_management.schemas import ScopeCategory
from src.server.scope_management.service import list_scopes, update_scope_category


def test_list_scopes_syncs_builtin_scopes(test_db_session: Session):
    scopes = list_scopes(test_db_session)

    assert len(scopes) == len(OAUTH2_SCOPES)
    assert {item.scope for item in scopes} == set(OAUTH2_SCOPES)

    password_scope = next(item for item in scopes if item.scope == "profile:password:write")
    assert password_scope.title == "修改密码"
    assert password_scope.description == "发起当前用户的密码修改流程。"
    assert password_scope.category == ScopeCategory.DANGEROUS


def test_update_scope_category(test_db_session: Session):
    updated = update_scope_category(
        test_db_session, "profile:read", ScopeCategory.SENSITIVE
    )

    assert updated.scope == "profile:read"
    assert updated.category == ScopeCategory.SENSITIVE


def test_update_unknown_scope_raises_not_found(test_db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        update_scope_category(
            test_db_session, "missing:scope", ScopeCategory.NORMAL
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "scope 不存在"


def test_list_scopes_migrates_legacy_defaults_to_new_default(test_db_session: Session):
    first_sync = list_scopes(test_db_session)
    password_scope = next(item for item in first_sync if item.scope == "profile:password:write")
    password_scope.category = ScopeCategory.SENSITIVE
    test_db_session.commit()

    second_sync = list_scopes(test_db_session)
    password_scope = next(item for item in second_sync if item.scope == "profile:password:write")
    assert password_scope.category == ScopeCategory.DANGEROUS

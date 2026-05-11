# -*- coding: utf-8 -*-
"""认证服务密码修改测试。"""

from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.service import (
    password_change_request_log,
    password_change_tokens,
    send_password_change_link,
    verify_password_change_token,
)


def test_password_change_link_token(test_db_session: Session):
    """测试密码修改确认 token"""
    password_change_tokens.clear()
    password_change_request_log.clear()

    # 准备测试数据
    user = User(username="testuser", email="test@example.com")
    user.set_password("oldpassword")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    token = send_password_change_link(
        user_id=user.id, email=user.email, app_domain="http://localhost:5173"
    )
    assert len(token) == 64

    resolved_user_id = verify_password_change_token(token)
    assert resolved_user_id == user.id

    reused_user_id = verify_password_change_token(token)
    assert reused_user_id is None

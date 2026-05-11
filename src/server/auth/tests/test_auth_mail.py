# -*- coding: utf-8 -*-
"""认证邮件模板测试。"""

from __future__ import annotations

from typing import Iterator

import pytest

from src.server.auth.service import password_change, password_reset, verification
from src.server.mail.schemas import MailContent, MailSendResult


@pytest.fixture(autouse=True)
def clear_auth_mail_state() -> Iterator[None]:
    verification.verification_codes.clear()
    password_reset.password_reset_tokens.clear()
    password_reset.password_reset_request_log.clear()
    password_change.password_change_tokens.clear()
    password_change.password_change_request_log.clear()
    yield
    verification.verification_codes.clear()
    password_reset.password_reset_tokens.clear()
    password_reset.password_reset_request_log.clear()
    password_change.password_change_tokens.clear()
    password_change.password_change_request_log.clear()


def test_send_verification_code_uses_html_mail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_mail: dict[str, MailContent] = {}

    def fake_send_mail(mail: MailContent) -> MailSendResult:
        sent_mail["mail"] = mail
        return MailSendResult(success=True, error=None)

    monkeypatch.setattr(verification, "is_mail_configured", lambda: True)
    monkeypatch.setattr(verification, "send_mail", fake_send_mail)

    code = verification.send_verification_code("alice@example.com")

    mail = sent_mail["mail"]
    assert len(code) == 6
    assert mail.subtype == "html"
    assert "Fullstack Template" in mail.body
    assert "请完成邮箱验证" in mail.body
    assert code in mail.body
    assert "验证码有效期 5 分钟" in mail.body


def test_send_password_reset_link_uses_html_mail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_mail: dict[str, MailContent] = {}

    def fake_send_mail(mail: MailContent) -> MailSendResult:
        sent_mail["mail"] = mail
        return MailSendResult(success=True, error=None)

    monkeypatch.setattr(password_reset, "is_mail_configured", lambda: True)
    monkeypatch.setattr(password_reset, "send_mail", fake_send_mail)

    token = password_reset.send_password_reset_link(
        "alice@example.com", "http://localhost:5173"
    )

    mail = sent_mail["mail"]
    reset_url = f"http://localhost:5173/reset-password/{token}"
    assert mail.subtype == "html"
    assert "重置您的登录密码" in mail.body
    assert "立即重置密码" in mail.body
    assert reset_url in mail.body
    assert "30 分钟" in mail.body


def test_send_password_change_link_uses_html_mail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_mail: dict[str, MailContent] = {}

    def fake_send_mail(mail: MailContent) -> MailSendResult:
        sent_mail["mail"] = mail
        return MailSendResult(success=True, error=None)

    monkeypatch.setattr(password_change, "is_mail_configured", lambda: True)
    monkeypatch.setattr(password_change, "send_mail", fake_send_mail)

    token = password_change.send_password_change_link(
        user_id=7, email="alice@example.com", app_domain="http://localhost:5173"
    )

    mail = sent_mail["mail"]
    change_url = f"http://localhost:5173/profile/password-change/{token}"
    assert mail.subtype == "html"
    assert "确认本次密码修改" in mail.body
    assert "确认并修改密码" in mail.body
    assert change_url in mail.body
    assert "30 分钟" in mail.body

# -*- coding: utf-8 -*-
"""
邮件发送服务测试（模板版）
"""

from __future__ import annotations

from email import message_from_string
import smtplib

import pytest

from src.server.mail import service
from src.server.mail.schemas import MailAddress, MailContent
from src.server.providers.constants import PROVIDER_MAIL
from src.server.providers.runtime import (
    clear_provider_runtime_configs,
    update_provider_runtime_config,
)
from src.server.providers.smtp.server import (
    MailMockServer,
    start as start_mail_mock_service,
)


class _FakeSMTP:
    """用于单测的 SMTP 替身，避免真实网络连接。"""

    last_instance: "_FakeSMTP | None" = None

    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args: tuple[str, str] | None = None
        self.sendmail_args: tuple[str, list[str], str] | None = None
        self.quit_called = False
        _FakeSMTP.last_instance = self

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, user: str, password: str) -> None:
        self.login_args = (user, password)

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> None:
        self.sendmail_args = (from_addr, to_addrs, msg)

    def quit(self) -> None:
        self.quit_called = True


class _FailingSMTP(_FakeSMTP):
    """用于单测的失败 SMTP 替身，模拟发送阶段异常。"""

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> None:
        raise RuntimeError("模拟 SMTP 发送失败")


class _DisconnectOnQuitSMTP(_FakeSMTP):
    """用于单测的 SMTP 替身，模拟发送成功后关闭连接时报断连。"""

    def quit(self) -> None:
        self.quit_called = True
        raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")


def test_send_mail_fail_when_sender_email_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.mail_config, "sender_email", None, raising=False)
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="a@example.com", name=None)],
    )
    result = service.MailSender().send(mail)

    assert result.success is False
    assert result.error is not None
    assert "未配置发件人邮箱（MAIL_SENDER_EMAIL）" in result.error


def test_send_mail_uses_mock_smtp_provider_in_test_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.mail_config, "sender_email", None, raising=False)
    monkeypatch.setattr(service.mail_config, "sender_password", None, raising=False)
    mock_service = start_mail_mock_service()
    update_provider_runtime_config(
        PROVIDER_MAIL,
        {
            "smtp_host": mock_service.config["smtp_host"],
            "smtp_port": mock_service.config["smtp_port"],
            "sender_email": "mock-sender@example.com",
            "sender_password": "",
        },
    )

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="a@example.com", name=None)],
    )
    try:
        result = service.send_mail(mail)
    finally:
        mock_service.shutdown()
        clear_provider_runtime_configs()

    assert result.success is True
    assert result.error is None
    assert MailMockServer.messages
    assert MailMockServer.messages[0][0] == "mock-sender@example.com"


def test_send_mail_fail_when_sender_password_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", None, raising=False)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="a@example.com", name=None)],
    )
    result = service.MailSender().send(mail)

    assert result.success is False
    assert result.error is not None
    assert "未配置发件人邮箱密码（MAIL_SENDER_PASSWORD）" in result.error


def test_send_mail_fail_when_smtp_sendmail_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_port", 465, raising=False)
    monkeypatch.setattr(service.mail_config, "timeout", 3, raising=False)
    monkeypatch.setattr(service.mail_config, "use_ssl", True, raising=False)
    monkeypatch.setattr(service.mail_config, "use_tls", False, raising=False)

    monkeypatch.setattr(service.smtplib, "SMTP_SSL", _FailingSMTP)
    monkeypatch.setattr(service.smtplib, "SMTP", _FailingSMTP)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="to@example.com", name=None)],
    )
    result = service.MailSender().send(mail)

    assert result.success is False
    assert result.error is not None
    assert "模拟 SMTP 发送失败" in result.error


def test_send_mail_success_via_fake_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_port", 465, raising=False)
    monkeypatch.setattr(service.mail_config, "timeout", 3, raising=False)
    monkeypatch.setattr(service.mail_config, "use_ssl", True, raising=False)
    monkeypatch.setattr(service.mail_config, "use_tls", False, raising=False)

    monkeypatch.setattr(service.smtplib, "SMTP_SSL", _FakeSMTP)
    monkeypatch.setattr(service.smtplib, "SMTP", _FakeSMTP)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="to@example.com", name="收件人")],
    )
    result = service.MailSender().send(mail)

    assert result.success is True
    assert result.error is None

    smtp = _FakeSMTP.last_instance
    assert smtp is not None
    assert smtp.login_args == ("sender@example.com", "pwd")
    assert smtp.sendmail_args is not None
    assert smtp.sendmail_args[0] == "sender@example.com"
    assert smtp.sendmail_args[1] == ["to@example.com"]
    assert "Subject" in smtp.sendmail_args[2]
    assert smtp.quit_called is True


def test_send_mail_success_with_html_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_port", 465, raising=False)
    monkeypatch.setattr(service.mail_config, "timeout", 3, raising=False)
    monkeypatch.setattr(service.mail_config, "use_ssl", True, raising=False)
    monkeypatch.setattr(service.mail_config, "use_tls", False, raising=False)

    monkeypatch.setattr(service.smtplib, "SMTP_SSL", _FakeSMTP)
    monkeypatch.setattr(service.smtplib, "SMTP", _FakeSMTP)

    mail = MailContent(
        subject="HTML 主题",
        body="<strong>HTML 正文</strong>",
        recipients=[MailAddress(email="to@example.com", name="收件人")],
        subtype="html",
    )
    result = service.MailSender().send(mail)

    assert result.success is True
    smtp = _FakeSMTP.last_instance
    assert smtp is not None
    assert smtp.sendmail_args is not None
    assert "Content-Type: text/html" in smtp.sendmail_args[2]
    mime_message = message_from_string(smtp.sendmail_args[2])
    payload = mime_message.get_payload(decode=True)
    assert isinstance(payload, bytes)
    assert payload.decode("utf-8") == "<strong>HTML 正文</strong>"


def test_send_mail_starttls_when_tls_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_port", 587, raising=False)
    monkeypatch.setattr(service.mail_config, "timeout", 3, raising=False)
    monkeypatch.setattr(service.mail_config, "use_ssl", False, raising=False)
    monkeypatch.setattr(service.mail_config, "use_tls", True, raising=False)

    monkeypatch.setattr(service.smtplib, "SMTP_SSL", _FakeSMTP)
    monkeypatch.setattr(service.smtplib, "SMTP", _FakeSMTP)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="to@example.com", name=None)],
    )
    result = service.MailSender().send(mail)

    assert result.success is True
    smtp = _FakeSMTP.last_instance
    assert smtp is not None
    assert smtp.started_tls is True


def test_send_mail_success_when_server_disconnects_on_quit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service.mail_config, "sender_email", "sender@example.com", raising=False
    )
    monkeypatch.setattr(service.mail_config, "sender_password", "pwd", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(service.mail_config, "smtp_port", 465, raising=False)
    monkeypatch.setattr(service.mail_config, "timeout", 3, raising=False)
    monkeypatch.setattr(service.mail_config, "use_ssl", True, raising=False)
    monkeypatch.setattr(service.mail_config, "use_tls", False, raising=False)

    monkeypatch.setattr(service.smtplib, "SMTP_SSL", _DisconnectOnQuitSMTP)
    monkeypatch.setattr(service.smtplib, "SMTP", _DisconnectOnQuitSMTP)

    mail = MailContent(
        subject="主题",
        body="正文",
        recipients=[MailAddress(email="to@example.com", name=None)],
    )
    result = service.MailSender().send(mail)

    assert result.success is True
    assert result.error is None

    smtp = _DisconnectOnQuitSMTP.last_instance
    assert smtp is not None
    assert smtp.sendmail_args is not None
    assert smtp.quit_called is True

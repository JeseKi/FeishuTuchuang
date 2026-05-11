# -*- coding: utf-8 -*-
"""SMTP mail external provider implementations."""

from __future__ import annotations

from abc import abstractmethod

from src.server.mail.schemas import MailContent, MailSendResult
from src.server.providers.base import ExternalProvider
from src.server.providers.constants import PROVIDER_MAIL
from src.server.providers.runtime import get_provider_runtime_config


class MailProvider(ExternalProvider):
    key = PROVIDER_MAIL
    label = "SMTP Mail"
    kind = "mail"

    @abstractmethod
    def send_mail(self, mail: MailContent) -> MailSendResult:
        """Send a mail message."""


class RealMailProvider(MailProvider):
    implementation = "real"

    def is_configured(self) -> bool:
        from src.server.mail.config import mail_config

        return bool(mail_config.sender_email and mail_config.sender_password)

    def send_mail(self, mail: MailContent) -> MailSendResult:
        from src.server.mail.service import MailSender

        return MailSender().send(mail)


class MockMailProvider(MailProvider):
    implementation = "mock"

    def is_configured(self) -> bool:
        config = get_provider_runtime_config(PROVIDER_MAIL)
        return bool(config.get("smtp_host") and config.get("smtp_port"))

    def send_mail(self, mail: MailContent) -> MailSendResult:
        from src.server.mail.config import MailConfig
        from src.server.mail.service import MailSender

        config = get_provider_runtime_config(PROVIDER_MAIL)
        mail_config = MailConfig(
            smtp_host=str(config.get("smtp_host") or "127.0.0.1"),
            smtp_port=int(config.get("smtp_port") or 1025),
            use_ssl=bool(config.get("use_ssl", False)),
            use_tls=bool(config.get("use_tls", False)),
            timeout=int(config.get("timeout") or 5),
            sender_email=str(config.get("sender_email") or "mock-sender@example.com"),
            sender_password=str(config.get("sender_password", "")),
            sender_name=str(config.get("sender_name") or "Mock Mail"),
        )
        return MailSender(mail_config).send(mail)

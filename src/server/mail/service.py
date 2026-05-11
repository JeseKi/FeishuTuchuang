# -*- coding: utf-8 -*-
"""
邮件发送服务（模板版）

公开接口：
- MailSender
- send_mail
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Iterable

from loguru import logger

from .config import mail_config, MailConfig
from .schemas import MailAddress, MailContent, MailSendResult


def _format_recipients(recipients: Iterable[MailAddress]) -> str:
    formatted = []
    for recipient in recipients:
        display_name = recipient.name or recipient.email
        formatted.append(formataddr((display_name, recipient.email)))
    return ", ".join(formatted)


def _build_mime_message(mail: MailContent, config: MailConfig) -> MIMEText:
    if not mail.recipients:
        raise ValueError("收件人列表不能为空")

    sender_email = config.sender_email
    if sender_email is None:
        raise ValueError("邮件发送配置缺失：未配置发件人邮箱（MAIL_SENDER_EMAIL）")

    message = MIMEText(mail.body, mail.subtype, "utf-8")
    sender_email_str = str(sender_email)
    sender_name = config.sender_name or sender_email_str
    message["From"] = formataddr((sender_name, sender_email_str))
    message["To"] = _format_recipients(mail.recipients)
    message["Subject"] = mail.subject
    return message


class MailSender:
    """邮件发送器（可作为依赖注入使用）"""

    def __init__(self, config: MailConfig | None = None) -> None:
        self._config = config or mail_config

    def send(self, mail: MailContent) -> MailSendResult:
        config = self._config

        try:
            message = _build_mime_message(mail, config)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"邮件内容构造失败：{exc}")
            return MailSendResult(success=False, error=str(exc))

        sender_email = config.sender_email
        if sender_email is None:
            error_msg = "邮件发送配置缺失：未配置发件人邮箱（MAIL_SENDER_EMAIL）"
            logger.error(error_msg)
            return MailSendResult(success=False, error=error_msg)
        sender_email_str = str(sender_email)

        sender_password = config.sender_password
        if sender_password is None:
            error_msg = "邮件发送配置缺失：未配置发件人邮箱密码（MAIL_SENDER_PASSWORD）"
            logger.error(error_msg)
            return MailSendResult(success=False, error=error_msg)

        smtp_class = smtplib.SMTP_SSL if config.use_ssl else smtplib.SMTP

        server: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        mail_sent = False
        send_error: Exception | None = None

        try:
            server = smtp_class(
                config.smtp_host,
                config.smtp_port,
                timeout=config.timeout,
            )
            if not config.use_ssl and config.use_tls:
                server.starttls()
            if sender_password:
                server.login(sender_email_str, sender_password)
            server.sendmail(
                sender_email_str,
                [recipient.email for recipient in mail.recipients],
                message.as_string(),
            )
            mail_sent = True
        except Exception as exc:  # noqa: BLE001
            send_error = exc
        finally:
            if server is not None:
                try:
                    server.quit()
                except smtplib.SMTPServerDisconnected as exc:
                    if mail_sent:
                        logger.warning(f"邮件发送成功，但服务器提前断开连接：{exc}")
                    else:
                        logger.debug(f"SMTP 连接在发送完成前断开：{exc}")
                except Exception as exc:  # noqa: BLE001
                    if mail_sent:
                        logger.warning(f"邮件发送成功，但关闭 SMTP 连接时出错：{exc}")
                    else:
                        logger.debug(f"发送失败后关闭 SMTP 连接也出错：{exc}")

        if send_error is not None:
            logger.error(f"邮件发送失败：{send_error}")
            return MailSendResult(success=False, error=str(send_error))

        return MailSendResult(success=True, error=None)


_default_sender = MailSender()


def send_mail(mail: MailContent) -> MailSendResult:
    """发送邮件（默认发送器）"""

    from src.server.providers import get_mail_provider

    return get_mail_provider().send_mail(mail)


__all__ = ["MailSender", "send_mail"]

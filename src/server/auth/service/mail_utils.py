# -*- coding: utf-8 -*-
"""认证服务邮件相关公共方法。"""

from src.server.mail.config import mail_config


def is_mail_configured() -> bool:
    return bool(mail_config.sender_email) and bool(mail_config.sender_password)

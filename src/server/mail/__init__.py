# -*- coding: utf-8 -*-
"""
邮件模块（模板版）

公开接口：
- MailAddress
- MailContent
- MailSendResult
- MailSender
- get_mail_sender
- send_mail
"""

from .schemas import MailAddress, MailContent, MailSendResult
from .service import MailSender, send_mail
from .dependencies import get_mail_sender

__all__ = [
    "MailAddress",
    "MailContent",
    "MailSendResult",
    "MailSender",
    "get_mail_sender",
    "send_mail",
]

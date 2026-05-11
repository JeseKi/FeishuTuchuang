# -*- coding: utf-8 -*-
"""
邮件依赖模块（模板版）

公开接口：
- get_mail_sender: 获取默认 MailSender 实例
"""

from functools import lru_cache

from .service import MailSender


@lru_cache
def get_mail_sender() -> MailSender:
    """获取默认 MailSender 实例，用于依赖注入。"""

    return MailSender()


__all__ = ["get_mail_sender"]

# -*- coding: utf-8 -*-
"""
邮件数据模型（模板版）

公开接口：
- MailAddress
- MailContent
- MailSendResult
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class MailAddress(BaseModel):
    """邮件地址信息"""

    email: EmailStr = Field(..., description="邮箱地址")
    name: str | None = Field(default=None, description="收件人名称", max_length=100)


class MailContent(BaseModel):
    """邮件正文内容"""

    subject: str = Field(..., min_length=1, max_length=120, description="邮件主题")
    body: str = Field(..., min_length=1, description="邮件正文")
    recipients: list[MailAddress] = Field(..., min_length=1, description="收件人列表")
    subtype: Literal["plain", "html"] = Field(
        default="plain", description="邮件正文格式"
    )


class MailSendResult(BaseModel):
    """邮件发送结果"""

    success: bool = Field(..., description="是否发送成功")
    error: str | None = Field(default=None, description="错误信息")


__all__ = ["MailAddress", "MailContent", "MailSendResult"]

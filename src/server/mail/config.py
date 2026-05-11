# -*- coding: utf-8 -*-
"""
邮件配置（模板版）

公开接口：
- mail_config
"""

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MailConfig(BaseSettings):
    """邮件发送配置"""

    smtp_host: str = Field(default="smtp.example.com", title="SMTP Host")
    smtp_port: int = Field(default=465, title="SMTP Port")
    use_ssl: bool = Field(default=True, title="使用 SSL")
    use_tls: bool = Field(default=False, title="使用 TLS")
    timeout: int = Field(default=5, title="SMTP 超时(秒)")
    sender_email: EmailStr | None = Field(
        default=None, title="发件人邮箱", description="必须配置"
    )
    sender_password: str | None = Field(
        default=None, title="发件人密码", description="必须配置"
    )
    sender_name: str | None = Field(
        default=None, title="发件人名称", description="可选"
    )

    model_config = SettingsConfigDict(
        env_prefix="MAIL_",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )


mail_config = MailConfig()

__all__ = ["MailConfig", "mail_config"]

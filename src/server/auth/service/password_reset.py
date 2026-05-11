# -*- coding: utf-8 -*-
"""密码重置相关服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast

from loguru import logger

from src.server.config import global_config
from src.server.mail import MailAddress, MailContent, send_mail

from .mail_utils import is_mail_configured
from .mail_templates import build_auth_email_html
from .tokens import generate_reset_token


PASSWORD_RESET_TOKEN_EXPIRES_MINUTES = 30
PASSWORD_RESET_TOKEN_SEND_COOLDOWN_SECONDS = 60

password_reset_tokens: dict[str, dict[str, str | datetime]] = {}
password_reset_request_log: dict[str, dict[str, datetime]] = {}


def send_password_reset_link(email: str, app_domain: str) -> str:
    """生成并发送密码重置链接邮件。"""
    now = datetime.now(timezone.utc)
    existing_data = password_reset_request_log.get(email)
    if existing_data is not None:
        last_sent = existing_data.get("sent_at")
        if isinstance(last_sent, datetime):
            elapsed_seconds = (now - last_sent).total_seconds()
            if elapsed_seconds < PASSWORD_RESET_TOKEN_SEND_COOLDOWN_SECONDS:
                retry_after_seconds = int(
                    PASSWORD_RESET_TOKEN_SEND_COOLDOWN_SECONDS - elapsed_seconds
                )
                retry_after_seconds = max(retry_after_seconds, 1)
                raise ValueError(f"发送过于频繁，请 {retry_after_seconds} 秒后再试")

    token = generate_reset_token()
    expires_minutes = PASSWORD_RESET_TOKEN_EXPIRES_MINUTES
    expiry = now + timedelta(minutes=expires_minutes)

    password_reset_tokens[token] = {"email": email, "expiry": expiry}
    password_reset_request_log[email] = {"sent_at": now}

    reset_base = app_domain.rstrip("/")
    reset_url = f"{reset_base}/reset-password/{token}"

    if not is_mail_configured():
        logger.warning("邮件配置为空，密码重置链接将打印到控制台中")
        logger.warning(f"邮箱 {email} 的重置链接：{reset_url}")
        return token

    mail = MailContent(
        subject="密码重置链接",
        body=build_auth_email_html(
            badge="密码重置",
            title="重置您的登录密码",
            preview_text="我们收到了密码重置请求，请在有效期内完成操作。",
            recipient_email=email,
            message="请点击下方按钮进入安全页面设置新的登录密码。为保护账户安全，本链接仅在短时间内有效。",
            highlight_label="链接有效期",
            highlight_value=f"{expires_minutes} 分钟",
            highlight_caption="请在有效期内完成密码重置，链接失效后需要重新申请。",
            tips=[
                "如果不是您本人发起的重置请求，请直接忽略此邮件。",
                "请不要将重置链接转发给他人，以免账户被盗用。",
            ],
            action_label="立即重置密码",
            action_url=reset_url,
        ),
        recipients=[MailAddress(email=email)],
        subtype="html",
    )
    mail_result = send_mail(mail)

    if not mail_result.success:
        logger.error(f"密码重置链接邮件发送失败：{mail_result.error}")
        if global_config.app_env not in {"dev", "test"}:
            password_reset_tokens.pop(token, None)
            password_reset_request_log.pop(email, None)
            raise RuntimeError("重置链接邮件发送失败")
        logger.warning("开发/测试环境忽略邮件发送失败，重置链接仍可使用")

    return token


def verify_password_reset_token(token: str) -> str | None:
    """验证密码重置 token 是否匹配且未过期，返回邮箱。"""
    stored_data = password_reset_tokens.get(token)
    if not stored_data:
        return None

    expiry = cast(datetime, stored_data["expiry"])
    if datetime.now(timezone.utc) >= expiry:
        password_reset_tokens.pop(token, None)
        return None

    email = cast(str, stored_data["email"])
    password_reset_tokens.pop(token, None)
    return email

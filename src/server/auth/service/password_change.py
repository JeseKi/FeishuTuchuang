# -*- coding: utf-8 -*-
"""密码修改确认相关服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast

from loguru import logger

from src.server.config import global_config
from src.server.mail import MailAddress, MailContent, send_mail

from .mail_utils import is_mail_configured
from .mail_templates import build_auth_email_html
from .tokens import generate_reset_token


PASSWORD_CHANGE_TOKEN_EXPIRES_MINUTES = 30
PASSWORD_CHANGE_TOKEN_SEND_COOLDOWN_SECONDS = 60

password_change_tokens: dict[str, dict[str, int | datetime]] = {}
password_change_request_log: dict[str, dict[str, datetime]] = {}


def send_password_change_link(user_id: int, email: str, app_domain: str) -> str:
    """生成并发送密码修改确认链接邮件。"""
    now = datetime.now(timezone.utc)
    request_key = str(user_id)
    existing_data = password_change_request_log.get(request_key)
    if existing_data is not None:
        last_sent = existing_data.get("sent_at")
        if isinstance(last_sent, datetime):
            elapsed_seconds = (now - last_sent).total_seconds()
            if elapsed_seconds < PASSWORD_CHANGE_TOKEN_SEND_COOLDOWN_SECONDS:
                retry_after_seconds = int(
                    PASSWORD_CHANGE_TOKEN_SEND_COOLDOWN_SECONDS - elapsed_seconds
                )
                retry_after_seconds = max(retry_after_seconds, 1)
                raise ValueError(f"发送过于频繁，请 {retry_after_seconds} 秒后再试")

    token = generate_reset_token()
    expires_minutes = PASSWORD_CHANGE_TOKEN_EXPIRES_MINUTES
    expiry = now + timedelta(minutes=expires_minutes)

    password_change_tokens[token] = {"user_id": user_id, "expiry": expiry}
    password_change_request_log[request_key] = {"sent_at": now}

    change_base = app_domain.rstrip("/")
    change_url = f"{change_base}/profile/password-change/{token}"

    if not is_mail_configured():
        logger.warning("邮件配置为空，密码修改确认链接将打印到控制台中")
        logger.warning(f"用户 {email} 的密码修改确认链接：{change_url}")
        return token

    mail = MailContent(
        subject="密码修改确认链接",
        body=build_auth_email_html(
            badge="密码修改确认",
            title="确认本次密码修改",
            preview_text="我们收到了修改密码请求，请先完成邮件确认。",
            recipient_email=email,
            message="请点击下方按钮确认本次密码修改请求。确认后，您将进入页面设置新的登录密码。",
            highlight_label="确认链接有效期",
            highlight_value=f"{expires_minutes} 分钟",
            highlight_caption="若超过有效期未确认，本次请求将自动失效。",
            tips=[
                "如果这不是您本人发起的操作，请忽略此邮件并尽快检查账户安全。",
                "请勿将确认链接分享给他人，以免影响账户安全。",
            ],
            action_label="确认并修改密码",
            action_url=change_url,
        ),
        recipients=[MailAddress(email=email)],
        subtype="html",
    )
    mail_result = send_mail(mail)

    if not mail_result.success:
        logger.error(f"密码修改确认链接邮件发送失败：{mail_result.error}")
        if global_config.app_env not in {"dev", "test"}:
            password_change_tokens.pop(token, None)
            password_change_request_log.pop(request_key, None)
            raise RuntimeError("密码修改确认链接发送失败")
        logger.warning("开发/测试环境忽略邮件发送失败，确认链接仍可使用")

    return token


def verify_password_change_token(token: str) -> int | None:
    """验证密码修改 token 是否匹配且未过期，返回用户 ID。"""
    stored_data = password_change_tokens.get(token)
    if not stored_data:
        return None

    expiry = cast(datetime, stored_data["expiry"])
    if datetime.now(timezone.utc) >= expiry:
        password_change_tokens.pop(token, None)
        return None

    user_id = int(cast(int, stored_data["user_id"]))
    password_change_tokens.pop(token, None)
    return user_id

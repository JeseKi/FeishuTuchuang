# -*- coding: utf-8 -*-
"""邮箱验证码相关服务。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
import string
from typing import cast

from loguru import logger

from src.server.config import global_config
from src.server.mail import MailAddress, MailContent, send_mail

from .mail_utils import is_mail_configured
from .mail_templates import build_auth_email_html


VERIFICATION_CODE_MAX_ATTEMPTS = 5
VERIFICATION_CODE_EXPIRES_MINUTES = 5
VERIFICATION_CODE_SEND_COOLDOWN_SECONDS = 60

verification_codes: dict[str, dict[str, str | datetime | int]] = {}


def generate_verification_code(length: int = 6) -> str:
    """生成指定长度的数字验证码。"""
    return "".join(random.choices(string.digits, k=length))


def send_verification_code(email: str) -> str:
    """生成并发送验证码邮件。"""
    now = datetime.now(timezone.utc)
    existing_data = verification_codes.get(email)
    if existing_data is not None:
        last_sent = existing_data.get("sent_at")
        if isinstance(last_sent, datetime):
            elapsed_seconds = (now - last_sent).total_seconds()
            if elapsed_seconds < VERIFICATION_CODE_SEND_COOLDOWN_SECONDS:
                retry_after_seconds = int(
                    VERIFICATION_CODE_SEND_COOLDOWN_SECONDS - elapsed_seconds
                )
                retry_after_seconds = max(retry_after_seconds, 1)
                raise ValueError(f"发送过于频繁，请 {retry_after_seconds} 秒后再试")

    code = generate_verification_code()
    expires_minutes = VERIFICATION_CODE_EXPIRES_MINUTES
    expiry = now + timedelta(minutes=expires_minutes)

    verification_codes[email] = {
        "code": code,
        "expiry": expiry,
        "sent_at": now,
        "attempts": 0,
    }

    if not is_mail_configured():
        logger.warning("邮件配置为空，验证码将打印到控制台中")
        logger.warning(f"邮箱 {email} 的验证码：{code}")
        return code

    mail = MailContent(
        subject="账户安全验证码",
        body=build_auth_email_html(
            badge="账户安全验证码",
            title="请完成邮箱验证",
            preview_text="您正在进行账号注册或安全验证，请使用验证码完成本次操作。",
            recipient_email=email,
            message="您正在进行账号注册或安全验证，请在页面中输入下方验证码以继续完成操作。",
            highlight_label="本次验证码",
            highlight_value=code,
            highlight_caption=f"验证码有效期 {expires_minutes} 分钟，请勿泄露给他人。",
            tips=[
                "如果这不是您本人发起的操作，请尽快修改账户密码或联系管理员。",
                "验证码仅用于当前一次验证流程，过期后需要重新申请。",
            ],
            highlight_is_code=True,
        ),
        recipients=[MailAddress(email=email)],
        subtype="html",
    )
    mail_result = send_mail(mail)

    if not mail_result.success:
        logger.error(f"验证码邮件发送失败：{mail_result.error}")
        if global_config.app_env not in {"dev", "test"}:
            verification_codes.pop(email, None)
            raise RuntimeError("验证码邮件发送失败")
        logger.warning("开发/测试环境忽略邮件发送失败，验证码仍可使用")

    return code


def verify_code(email: str, code: str) -> bool:
    """验证邮箱和验证码是否匹配且未过期。"""
    stored_data = verification_codes.get(email)
    if not stored_data:
        return False

    stored_code = stored_data["code"]
    expiry = cast(datetime, stored_data["expiry"])
    attempts = int(cast(int, stored_data.get("attempts", 0)))

    if datetime.now(timezone.utc) >= expiry:
        verification_codes.pop(email, None)
        return False

    if stored_code == code:
        verification_codes.pop(email, None)
        return True

    attempts += 1
    if attempts >= VERIFICATION_CODE_MAX_ATTEMPTS:
        verification_codes.pop(email, None)
        return False

    stored_data["attempts"] = attempts
    return False

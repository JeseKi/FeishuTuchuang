# -*- coding: utf-8 -*-
"""认证邮件 HTML 模板。"""

from __future__ import annotations

from html import escape
from typing import Iterable


def _render_tips(tips: Iterable[str]) -> str:
    rendered_items: list[str] = []
    for tip in tips:
        rendered_items.append(
            (
                '<li style="margin:0 0 10px 0;color:#475569;line-height:1.75;">'
                f"{escape(tip)}"
                "</li>"
            )
        )
    if not rendered_items:
        return ""

    return (
        '<div style="margin-top:24px;">'
        '<div style="font-size:13px;font-weight:700;letter-spacing:0.04em;'
        'text-transform:uppercase;color:#0f172a;">安全提示</div>'
        '<ul style="margin:12px 0 0 20px;padding:0;">'
        f"{''.join(rendered_items)}"
        "</ul>"
        "</div>"
    )


def _render_action(action_label: str | None, action_url: str | None) -> str:
    if not action_label or not action_url:
        return ""

    safe_label = escape(action_label)
    safe_url = escape(action_url, quote=True)
    return (
        '<div style="margin-top:24px;">'
        f'<a href="{safe_url}" '
        'style="display:inline-block;padding:14px 22px;border-radius:14px;'
        "background:#0ea5e9;color:#ffffff;text-decoration:none;"
        'font-size:15px;font-weight:700;">'
        f"{safe_label}"
        "</a>"
        '<div style="margin-top:14px;font-size:13px;line-height:1.75;'
        'color:#64748b;">'
        "如果按钮无法打开，请复制以下链接到浏览器访问："
        "</div>"
        '<div style="margin-top:8px;padding:14px 16px;border-radius:14px;'
        "background:#f8fafc;border:1px solid #e2e8f0;font-size:13px;"
        'line-height:1.75;word-break:break-all;color:#0369a1;">'
        f"{safe_url}"
        "</div>"
        "</div>"
    )


def build_auth_email_html(
    *,
    badge: str,
    title: str,
    preview_text: str,
    recipient_email: str,
    message: str,
    highlight_label: str,
    highlight_value: str,
    highlight_caption: str,
    tips: Iterable[str],
    action_label: str | None = None,
    action_url: str | None = None,
    highlight_is_code: bool = False,
) -> str:
    """构造统一风格的认证邮件 HTML。"""

    safe_badge = escape(badge)
    safe_title = escape(title)
    safe_preview = escape(preview_text)
    safe_recipient_email = escape(recipient_email)
    safe_message = escape(message)
    safe_highlight_label = escape(highlight_label)
    safe_highlight_value = escape(highlight_value)
    safe_highlight_caption = escape(highlight_caption)

    value_style = (
        "margin-top:10px;font-size:40px;font-weight:800;line-height:1.1;color:#0f172a;"
    )
    if highlight_is_code:
        value_style += "font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;letter-spacing:6px;"

    return (
        "<!DOCTYPE html>"
        '<html lang="zh-CN">'
        "<head>"
        '<meta charset="utf-8" />'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />'
        '<meta name="color-scheme" content="light only" />'
        f"<title>{safe_title}</title>"
        "</head>"
        '<body style="margin:0;padding:0;background:#e2e8f0;">'
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{safe_preview}</div>'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" '
        'style="background:linear-gradient(180deg,#e0f2fe 0%,#f8fafc 45%,#e2e8f0 100%);">'
        "<tr>"
        '<td align="center" style="padding:32px 16px;">'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" '
        'style="max-width:680px;">'
        "<tr>"
        '<td style="padding-bottom:16px;">'
        '<div style="display:inline-block;padding:8px 14px;border-radius:999px;'
        "background:rgba(14,165,233,0.12);color:#0369a1;font-size:12px;"
        'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">'
        "Fullstack Template"
        "</div>"
        "</td>"
        "</tr>"
        "<tr>"
        '<td style="padding:32px;border-radius:28px;background:linear-gradient(135deg,#0f172a 0%,#0f766e 100%);'
        'box-shadow:0 24px 60px rgba(15,23,42,0.18);">'
        f'<div style="font-size:13px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#7dd3fc;">{safe_badge}</div>'
        f'<div style="margin-top:14px;font-size:32px;font-weight:800;line-height:1.2;color:#ffffff;">{safe_title}</div>'
        f'<div style="margin-top:14px;font-size:16px;line-height:1.75;color:#cbd5e1;">{safe_preview}</div>'
        "</td>"
        "</tr>"
        "<tr>"
        '<td style="padding-top:20px;">'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" '
        'style="background:#ffffff;border:1px solid rgba(148,163,184,0.22);'
        'border-radius:28px;box-shadow:0 18px 48px rgba(15,23,42,0.10);">'
        "<tr>"
        '<td style="padding:32px;">'
        f'<div style="font-size:16px;font-weight:700;color:#0f172a;">您好，{safe_recipient_email}</div>'
        f'<div style="margin-top:12px;font-size:15px;line-height:1.8;color:#334155;">{safe_message}</div>'
        '<div style="margin-top:24px;padding:22px 24px;border-radius:22px;'
        'border:1px solid #dbeafe;background:linear-gradient(180deg,#f8fafc 0%,#eff6ff 100%);">'
        f'<div style="font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#0369a1;">{safe_highlight_label}</div>'
        f'<div style="{value_style}">{safe_highlight_value}</div>'
        f'<div style="margin-top:10px;font-size:14px;line-height:1.75;color:#475569;">{safe_highlight_caption}</div>'
        "</div>"
        f"{_render_action(action_label, action_url)}"
        f"{_render_tips(tips)}"
        '<div style="margin-top:28px;padding-top:20px;border-top:1px solid #e2e8f0;'
        'font-size:13px;line-height:1.8;color:#64748b;">'
        "此邮件由系统自动发送，请勿直接回复。"
        "</div>"
        "</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "</table>"
        "</body>"
        "</html>"
    )

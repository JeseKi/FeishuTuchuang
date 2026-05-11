# SMTP Mail Provider

创建时间：2026-05-01  
更新时间：2026-05-01

## Provider

- Provider key: `mail`
- Real provider: `mail.py`
- Mock service: `server.py`
- 后端请求协议：SMTP

## Mock Service

mock service 启动本地 SMTP server，后端在 mock 模式下仍然通过 `smtplib` 发送邮件。

当前 mock SMTP server 不要求 AUTH，runtime config 会把 `sender_password` 设为空字符串，使 `MailSender` 跳过登录但保留真实 SMTP 发送流程。

mock service 同时启动一个 HTTP inbox 页面，脚本会输出 `inbox_url`。邮件仅存储在当前进程内存中，重启后清空。

## 官方文档

- SMTP RFC 5321: https://www.rfc-editor.org/rfc/rfc5321
- Internet Message Format RFC 5322: https://www.rfc-editor.org/rfc/rfc5322

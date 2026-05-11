# Google OAuth Provider

创建时间：2026-05-01  
更新时间：2026-05-01

## Provider

- Provider key: `google_oauth`
- Real provider: `oauth.py`
- Mock service: `server.py`
- 后端请求协议：HTTP OAuth/OIDC userinfo

## Mock Service

mock service 实现当前后端用到的 Google OAuth 2.0 Web Server flow 和 userinfo 调用：

- `GET /o/oauth2/v2/auth`
- `POST /token`
- `GET /userinfo`

后端在 mock 模式下仍然通过 HTTP 调用这些端点，并校验 `email_verified` 等字段。

访问 `GET /o/oauth2/v2/auth` 时会显示一个简单授权确认页，点击“允许授权”后再携带 authorization code 回跳到应用 callback。

## 官方文档

- Google OAuth 2.0 Web Server Applications: https://developers.google.com/identity/protocols/oauth2/web-server
- Google OpenID Connect: https://developers.google.com/identity/openid-connect/openid-connect

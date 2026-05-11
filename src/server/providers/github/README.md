# GitHub OAuth Provider

创建时间：2026-05-01  
更新时间：2026-05-01

## Provider

- Provider key: `github_oauth`
- Real provider: `oauth.py`
- Mock service: `server.py`
- 后端请求协议：HTTP OAuth/API

## Mock Service

mock service 实现当前后端用到的 GitHub OAuth Web application flow：

- `GET /login/oauth/authorize`
- `POST /login/oauth/access_token`
- `GET /user`
- `GET /user/emails`

后端在 mock 模式下仍然通过 HTTP 调用这些端点，并解析 mock service 返回的数据。

访问 `GET /login/oauth/authorize` 时会显示一个简单授权确认页，点击“允许授权”后再携带 authorization code 回跳到应用 callback。

## 官方文档

- GitHub OAuth Apps authorization: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
- GitHub REST Users API: https://docs.github.com/en/rest/users/users

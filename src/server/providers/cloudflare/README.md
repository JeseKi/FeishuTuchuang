# Cloudflare Turnstile Provider

创建时间：2026-05-01  
更新时间：2026-05-01

## Provider

- Provider key: `turnstile`
- Real provider: `turnstile.py`
- Mock service: `server.py`
- 后端请求协议：HTTP Siteverify

## Mock Service

mock service 实现当前后端用到的 Turnstile server-side validation：

- `POST /turnstile/v0/siteverify`

当 token 为 `mock-fail` 时返回失败响应，其余 token 返回成功响应。后端在 mock 模式下仍然发起 HTTP siteverify 请求。

前端开发时可设置：

```env
TURNSTILE_ENABLED=true
EXTERNAL_PROVIDER_MOCK_LIST=["turnstile"]
```

启动后端和 `scripts/mock_provider_services.py` 后，前端会从 `GET /api/dev/providers/frontend-config` 读取 mock site key 和固定 script URL。浏览器加载的是后端固定路径 `/api/dev/providers/turnstile/api.js`，后端再代理到随机端口上的 mock service。

此时登录、注册和重置密码页面会显示一个本地校验按钮。点击后前端提交 mock token，后端仍然请求本地 mock service 的 siteverify API。

## 官方文档

- Cloudflare Turnstile server-side validation: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/

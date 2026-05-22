# 常见问题

## 文档地址返回前端首页

确认 `.env` 中已经设置：

```ini
ENABLE_DOCS=true
```

并且镜像已重新构建：

```bash
docker compose up -d --build
```

## 文档地址 404

确认访问路径包含结尾斜杠：

```text
/mkdocs/docs/
```

如果仍然 404，检查镜像构建时 `mkdocs build --strict` 是否成功。

## 飞书 OAuth 回调失败

检查飞书开放平台中的重定向地址是否和实际部署域名一致：

```text
https://img.example.com/api/images/feishu/oauth/callback
```

同时确认 `.env` 中：

```ini
APP_DOMAIN=https://img.example.com
IMAGE_HOST_PUBLIC_BASE_URL=https://img.example.com
```

## 图片公开 URL 无法访问

先检查健康检查接口：

```text
/api/health
```

再检查：

- `IMAGE_HOST_PUBLIC_BASE_URL` 是否是外部可访问地址。
- 反向代理是否把请求转发到容器的 `8000` 端口。
- 飞书授权是否已完成，目标文件夹是否可用。

## 上传文件过大

应用侧限制由 `IMAGE_HOST_MAX_UPLOAD_MB` 控制。反向代理也需要设置足够的上传限制，例如 Nginx 的 `client_max_body_size`。

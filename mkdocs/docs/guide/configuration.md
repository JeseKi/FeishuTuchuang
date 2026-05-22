# 配置

配置通过 `.env` 注入。可以从 `.env.example` 复制后修改：

```bash
cp .env.example .env
```

## 基础配置

```ini
APP_ENV=prod
PORT=8000
APP_DOMAIN=https://img.example.com
APP_SECRET_KEY=替换成随机长字符串
ALLOWED_ORIGINS=["https://img.example.com"]
```

`APP_DOMAIN` 用于生成密码重置、飞书 OAuth 回调等外部链接。生产环境应配置为 HTTPS 域名。

## 数据库与日志

```ini
DATABASE_PATH=data/database.db
LOG_LEVEL=info
LOG_DIR=logs
LOG_ROTATION=20 MB
LOG_RETENTION=14 days
LOG_SERIALIZE=false
```

## 管理员账号

```ini
INIT_ADMIN_NAME=admin
INIT_ADMIN_PASSWORD=替换成强密码
INIT_ADMIN_EMAIL=admin@example.com
ENABLE_PUBLIC_REGISTRATION=false
```

公开注册默认关闭。需要多人使用时，建议管理员在后台创建用户；如果确实要开放注册，再配置 SMTP 和 Turnstile：

```ini
ENABLE_PUBLIC_REGISTRATION=true
MAIL_SENDER_EMAIL=your-sender@example.com
MAIL_SENDER_PASSWORD=your-smtp-password
TURNSTILE_ENABLED=true
TURNSTILE_SECRET_KEY=your-turnstile-secret
VITE_TURNSTILE_SITE_KEY=your-turnstile-site-key
```

## 飞书图床

```ini
IMAGE_HOST_FEISHU_APP_ID=
IMAGE_HOST_FEISHU_APP_SECRET=
IMAGE_HOST_FEISHU_API_BASE_URL=https://open.feishu.cn/open-apis
IMAGE_HOST_FEISHU_OAUTH_SCOPE=offline_access drive:drive
IMAGE_HOST_PUBLIC_BASE_URL=https://img.example.com
```

## 内置文档

```ini
ENABLE_DOCS=false
```

设置为 `true` 后，后端会把 MkDocs 构建产物挂载到 `/mkdocs/docs/`。

## 兼容开关

开源默认只暴露图床所需能力，旧模板能力默认关闭：

```ini
ENABLE_EXAMPLE_MODULE=false
ENABLE_OAUTH_LOGIN=false
ENABLE_OAUTH_PROVIDER=false
ENABLE_SCOPE_MANAGEMENT=false
ENABLE_DEV_PROVIDER_RUNTIME=false
ENABLE_EXTERNAL_PROVIDER_REGISTRY=false
```

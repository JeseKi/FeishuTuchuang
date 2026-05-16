# Feishu Image Host

自托管飞书图床。图片上传到飞书 Drive，本机磁盘作为热缓存，对外提供稳定的图片访问 URL。

默认开源形态聚焦个人和小团队自托管：公开注册关闭，由管理员创建用户；模板时期的示例模块、OAuth Provider、Scope 管理和开发 Provider Runtime 代码仍保留，但默认不挂载路由、不显示入口。

## Features

- 飞书 Drive 冷存储：通过飞书用户 OAuth 授权上传、下载、删除和移动图片。
- 本地热缓存：公开访问 `/i/{filename}` 时优先命中本地缓存，缺失时从飞书回源。
- 图片管理台：上传图片、筛选历史、预览、复制 URL、管理飞书目标文件夹。
- API Key 集成：支持 `/api/v1/images` 和 `/api/v2/images` 给外部工具上传图片。
- 自托管账号：管理员引导、登录、刷新令牌、个人资料、密码修改、TOTP 2FA、设备管理。
- SQLite + Alembic：默认写入 `data/database.db`，容器启动会执行迁移。

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pnpm install
cp .env.example .env
```

编辑 `.env`：

```ini
APP_SECRET_KEY=replace-with-random-secret
INIT_ADMIN_NAME=admin
INIT_ADMIN_PASSWORD=replace-with-strong-password
INIT_ADMIN_EMAIL=admin@example.com
IMAGE_HOST_FEISHU_APP_ID=
IMAGE_HOST_FEISHU_APP_SECRET=
IMAGE_HOST_PUBLIC_BASE_URL=http://localhost:8000
```

启动开发环境：

```bash
.venv/bin/python run.py
pnpm dev
```

默认地址：

- 前端开发服务器：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- 健康检查：`http://localhost:8000/api/health`

## Feishu Setup

1. 在飞书开放平台创建应用，填入 `IMAGE_HOST_FEISHU_APP_ID` 和 `IMAGE_HOST_FEISHU_APP_SECRET`。
2. 配置重定向地址：`{IMAGE_HOST_PUBLIC_BASE_URL}/api/images/feishu/oauth/callback`。
3. 开通 Drive 文件上传、下载、删除、移动相关权限。
4. 启动服务后使用管理员账号登录，进入“飞书图床”，完成飞书 Drive 授权。
5. 在“飞书文件夹”中添加可上传的 folder token；未配置时会尝试使用 Drive 根目录。

## Configuration

常用配置见 `.env.example`。开源默认值只暴露图床所需能力：

```ini
ENABLE_PUBLIC_REGISTRATION=false
ENABLE_EXAMPLE_MODULE=false
ENABLE_OAUTH_LOGIN=false
ENABLE_OAUTH_PROVIDER=false
ENABLE_SCOPE_MANAGEMENT=false
ENABLE_DEV_PROVIDER_RUNTIME=false
ENABLE_EXTERNAL_PROVIDER_REGISTRY=false
```

如果你想继续使用模板时期的扩展能力，可以显式打开对应开关。默认不建议公网暴露这些能力，除非你会维护对应安全边界和文档。

公开注册默认关闭。需要多人使用时，建议管理员在后台创建用户；如果确实要开放注册，再设置：

```ini
ENABLE_PUBLIC_REGISTRATION=true
MAIL_SENDER_EMAIL=your-sender@example.com
MAIL_SENDER_PASSWORD=your-smtp-password
TURNSTILE_ENABLED=true
TURNSTILE_SECRET_KEY=your-turnstile-secret
VITE_TURNSTILE_SITE_KEY=your-turnstile-site-key
```

## API

网页管理接口需要登录态；外部集成接口使用 `X-API-Key` 或 `Authorization: Bearer <api_key>`。

```bash
curl -X POST http://localhost:8000/api/v2/images \
  -H "X-API-Key: $API_KEY" \
  -F "folder_name=default" \
  -F "image=@./demo.png"

curl http://localhost:8000/i/{filename}
```

## Deployment

Docker Compose：

```bash
docker compose up -d --build
```

容器行为：

- 构建前端产物并由 FastAPI 托管。
- 启动时执行 `alembic upgrade head`。
- 默认挂载 `./data:/app/data` 和 `./logs:/app/logs`。

## Development

后端开发结构参考 `src/server/example_module`，但开源默认不会挂载示例模块路由。

测试：

```bash
.venv/bin/python -m pytest . -q
pnpm lint
```

常用命令：

```bash
.venv/bin/python scripts/init_db.py --check
.venv/bin/python scripts/init_db.py --reset
pnpm build
```

## Open Source Notes

- `.env`、`data/`、`logs/`、`dist/` 默认不应提交。
- 开源前请轮换本地飞书 App Secret、OAuth token、folder token 和管理员密码。
- 历史 Alembic 迁移保持兼容，不会删除旧表；隐藏功能的代码保留给需要二次开发的人。

## License

MIT

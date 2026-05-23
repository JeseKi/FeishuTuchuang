# Feishu Image Host

![banner](https://fstc.kispace.cc/i/ebe8a14c823fbb2b110d4066459c4250.png)
<video controls="controls" src="https://fstc.kispace.cc/i/0592bddd3028bf5dae13a4956f09939a.mp4"></video>

自托管飞书图床。图片上传到飞书 Drive，本机磁盘作为热缓存，对外提供稳定的图片访问 URL。

默认形态适合个人和小团队部署：公开注册关闭，由管理员创建用户；模板时期的示例模块、OAuth Provider、Scope 管理和开发 Provider Runtime 代码仍保留，但默认不挂载路由、不显示入口。

## 功能

- 飞书 Drive 冷存储：通过飞书用户 OAuth 授权上传、下载、删除和移动图片。
- 本地热缓存：公开访问 `/i/{filename}` 时优先命中本地缓存，缺失时从飞书回源。
- 图片管理台：上传图片、筛选历史、预览、复制 URL、管理飞书目标文件夹。
- API Key 集成：支持 `/api/v1/images` 和 `/api/v2/images` 给外部工具上传图片。
- 自托管账号：管理员引导、登录、刷新令牌、个人资料、密码修改、TOTP 2FA、设备管理。
- SQLite + Alembic：默认写入 `data/database.db`，容器启动会执行迁移并备份现有数据库。

## 部署前准备

### 1. 准备服务器

最低建议：

- Linux 服务器一台
- Docker 与 Docker Compose
- 一个能访问服务器的域名，例如 `https://img.example.com`
- 可选：Nginx / Caddy / Traefik 做 HTTPS 反向代理

如果只在内网使用，也可以直接暴露 `http://服务器IP:8000`。

### 2. 创建飞书应用

在飞书开放平台创建企业自建应用，并完成这些配置：

1. 记录应用的 `App ID` 和 `App Secret`，分别填入 `IMAGE_HOST_FEISHU_APP_ID` 和 `IMAGE_HOST_FEISHU_APP_SECRET`。
2. 配置重定向地址：

```text
https://img.example.com/api/images/feishu/oauth/callback
```

如果本地测试，则使用：

```text
http://localhost:8000/api/images/feishu/oauth/callback
```

3. 开通 Drive 文件上传、下载、删除、移动相关权限。
4. 发布或启用应用权限变更，确保当前企业内可授权。

## Docker Compose 部署

### 1. 克隆并创建配置

```bash
git clone <your-repo-url> feishu-image-host
cd feishu-image-host
cp .env.example .env
```

编辑 `.env`，至少修改这些值：

```ini
APP_ENV=prod
APP_DOMAIN=https://img.example.com
APP_SECRET_KEY=替换成随机长字符串

INIT_ADMIN_NAME=admin
INIT_ADMIN_PASSWORD=替换成强密码
INIT_ADMIN_EMAIL=admin@example.com

IMAGE_HOST_FEISHU_APP_ID=飞书应用 App ID
IMAGE_HOST_FEISHU_APP_SECRET=飞书应用 App Secret
IMAGE_HOST_PUBLIC_BASE_URL=https://img.example.com
```

生产环境不要使用示例密码。`APP_SECRET_KEY` 和 `TWO_FACTOR_ENCRYPTION_KEY` 都应使用随机长字符串。

### 2. 启动服务

```bash
docker compose up -d --build
```

默认容器监听宿主机 `8000` 端口：

```text
http://服务器IP:8000
```

容器会挂载：

- `./data:/app/data`：SQLite 数据库和图片缓存
- `./logs:/app/logs`：应用日志

容器启动时会：

- 构建前端静态产物
- 检查并备份现有 SQLite 数据库
- 执行 `alembic upgrade head`
- 启动 FastAPI，并由后端托管前端页面

### 3. 配置 HTTPS 反向代理

以 Nginx 为例：

```nginx
server {
    listen 80;
    server_name img.example.com;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

建议在反向代理层配置 HTTPS 证书，并把 `.env` 中的 `APP_DOMAIN` 和 `IMAGE_HOST_PUBLIC_BASE_URL` 设置为 HTTPS 域名。

## 首次初始化

1. 打开 `https://img.example.com`。
2. 使用 `.env` 中的 `INIT_ADMIN_NAME` 和 `INIT_ADMIN_PASSWORD` 登录。
3. 进入“飞书图床”，点击飞书授权，完成 Drive OAuth 授权。
4. 在“飞书文件夹”中添加可上传的 folder token。
5. 上传一张图片，确认返回的公开 URL 可以访问。

如果没有配置飞书文件夹，系统会尝试使用 Drive 根目录；更推荐创建专用文件夹并在后台配置 folder token。

## 常用运维命令

查看日志：

```bash
docker compose logs -f app
```

重启：

```bash
docker compose restart app
```

更新代码并重新构建：

```bash
git pull
docker compose up -d --build
```

备份数据：

```bash
tar czf feishu-image-host-data-$(date +%F).tar.gz data logs .env
```

恢复时，把 `data/`、`logs/` 和 `.env` 放回项目目录，再执行：

```bash
docker compose up -d --build
```

## 配置说明

常用配置见 `.env.example`。开源默认只暴露图床所需能力：

```ini
ENABLE_PUBLIC_REGISTRATION=false
ENABLE_EXAMPLE_MODULE=false
ENABLE_OAUTH_LOGIN=false
ENABLE_OAUTH_PROVIDER=false
ENABLE_SCOPE_MANAGEMENT=false
ENABLE_DEV_PROVIDER_RUNTIME=false
ENABLE_EXTERNAL_PROVIDER_REGISTRY=false
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

## API 集成

网页管理接口需要登录态；外部集成接口使用 `X-API-Key` 或 `Authorization: Bearer <api_key>`。

```bash
curl -X POST https://img.example.com/api/v2/images \
  -H "X-API-Key: $API_KEY" \
  -F "folder_name=default" \
  -F "image=@./demo.png"

curl https://img.example.com/i/{filename}
```

## 本地开发

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pnpm install
cp .env.example .env
.venv/bin/python run.py
pnpm dev
```

默认地址：

- 前端开发服务器：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- 健康检查：`http://localhost:8000/api/health`

测试：

```bash
.venv/bin/python -m pytest . -q
pnpm lint
pnpm build
```

## License

MIT

## Friendly Links

- [LINUX DO - 新的理想型社区](https://linux.do/)
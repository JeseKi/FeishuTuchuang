# 部署

## 准备服务器

最低建议：

- Linux 服务器一台
- Docker 与 Docker Compose
- 一个能访问服务器的域名，例如 `https://img.example.com`
- 可选：Nginx、Caddy 或 Traefik 做 HTTPS 反向代理

如果只在内网使用，也可以直接暴露 `http://服务器IP:8000`。

## 克隆并创建配置

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

## 启动服务

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

## 配置 HTTPS 反向代理

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

## 启用内置文档

默认不暴露内置文档站点。需要启用时，在 `.env` 中设置：

```ini
ENABLE_DOCS=true
```

重新构建并启动容器后，访问：

```text
http://服务器IP:8000/mkdocs/docs/
```

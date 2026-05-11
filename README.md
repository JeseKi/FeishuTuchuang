# Fullstack Template

基于 FastAPI + React + Vite 的全栈模板，内置认证、管理员用户管理、示例业务模块、SQLite、本地日志、前端打包产物托管，以及一套可直接运行的测试样例。

这个仓库的开发模式是：

- 开发环境下，前后端分别启动
- 构建或容器部署后，由 FastAPI 直接托管 `dist/` 中的前端 SPA

## 功能概览

- 用户认证：注册、登录、刷新令牌、个人资料、修改密码、TOTP 双因素认证（含 backup codes）
- OAuth 登录：支持通过 `OAUTH_LIST` 选择性启用 GitHub / Google OAuth 登录
- 密码重置：支持发送重置链接与基于 token 的重置流程
- 管理员功能：查看用户列表、更新用户角色/状态/基础信息
- 默认管理员引导：首次初始化数据库时自动创建管理员账号
- 示例业务模块：提供独立的 router / service / dao / tests 结构
- 外部 Provider：支持 GitHub、Google、Turnstile、SMTP、示例外部 API 的 real/mock target 切换
- SQLite 持久化：默认数据库文件为 `data/database.db`
- 日志能力：应用日志、访问日志、错误日志写入 `logs/`
- SPA 托管：后端在检测到 `dist/` 后会挂载前端静态资源
- 测试样例：后端模块已附带 pytest 测试

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic Settings、Alembic、python-jose、bcrypt、Loguru
- 前端：React 19、Vite 7、React Router 7、Tailwind CSS 4、Ant Design、Axios、TypeScript 5
- 工具链：pnpm、pytest、mypy、ruff、ESLint、Docker、docker compose

## 目录结构

```text
.
├── .env.example
├── Dockerfile
├── Makefile
├── README.md
├── alembic/
├── data/                         # SQLite 数据目录
├── dist/                         # 前端构建产物（构建后生成）
├── logs/                         # 日志目录
├── run.py                        # 本地后端启动入口
├── scripts/
│   ├── init_db.py                # 数据库初始化 / 检查 / 重置脚本
│   └── mock_provider_services.py # 本地 mock provider 一键启动脚本
├── src/
│   ├── client/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── providers/
│   └── server/
│       ├── admin/                # 管理员接口
│       ├── auth/                 # 认证与密码重置
│       ├── example_module/       # 示例模块
│       ├── providers/            # 外部服务 provider 与本地 mock services
│       ├── config.py
│       ├── database.py
│       └── main.py
├── vite.config.ts
└── package.json
```

## 环境要求

- Python 3.11+
- Node.js 18+
- pnpm

容器镜像当前使用：

- 前端构建阶段：Node 23
- 后端运行阶段：Python 3.11 slim

## 快速开始

### 方式一：使用 Makefile

```bash
make setup
cp .env.example .env
make dev
```

前端开发服务器需要单独启动：

```bash
pnpm dev
```

### 方式二：手动启动

1. 创建并安装 Python 虚拟环境

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. 安装前端依赖

```bash
pnpm install
```

3. 准备环境变量

```bash
cp .env.example .env
```

4. 启动后端

```bash
.venv/bin/python run.py
```

5. 启动前端

```bash
pnpm dev
```

默认地址：

- 前端开发环境：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- 健康检查：`http://localhost:8000/api/health`

## 环境变量

`.env.example` 已提供默认值。常用配置如下：

```ini
APP_ENV=dev
ALLOWED_ORIGINS=["http://localhost:5173"]
OAUTH_LIST=[]
EXTERNAL_PROVIDER_MOCK_LIST=[]
MOCK_PROVIDER_BACKEND_URL=http://localhost:8000
MOCK_PROVIDER_PUBLISH_INTERVAL_SECONDS=2
APP_SECRET_KEY=change-me
DATABASE_PATH=data/database.db
PORT=8000
LOG_LEVEL=info
LOG_DIR=logs
LOG_ROTATION=20 MB
LOG_RETENTION=14 days
LOG_SERIALIZE=false
VITE_API_BASE_URL=/api
# 前端 Turnstile 站点 Key；dev mock 模式会优先从后端 runtime config 读取
VITE_TURNSTILE_SITE_KEY=

# 后端 Turnstile 校验开关
TURNSTILE_ENABLED=false
TURNSTILE_SECRET_KEY=
TURNSTILE_VERIFY_TIMEOUT_SECONDS=4

INIT_ADMIN_NAME=admin
INIT_ADMIN_PASSWORD=admin123
INIT_ADMIN_EMAIL=admin@example.com
MAIL_SMTP_HOST=smtp.example.com
MAIL_SMTP_PORT=465
MAIL_USE_SSL=true
MAIL_USE_TLS=false
MAIL_TIMEOUT=5
MAIL_SENDER_EMAIL=
MAIL_SENDER_PASSWORD=
MAIL_SENDER_NAME=
APP_DOMAIN=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/api/oauth/github/callback
GITHUB_SCOPE=read:user user:email
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback
GOOGLE_SCOPE=openid email profile
EXAMPLE_EXTERNAL_API_BASE_URL=
TWO_FACTOR_CHALLENGE_TTL_MINUTES=5
TWO_FACTOR_SETUP_TTL_MINUTES=10
TWO_FACTOR_ISSUER_NAME=Fullstack Template
TWO_FACTOR_ENCRYPTION_KEY=change-me-in-production
TWO_FACTOR_BACKUP_CODE_COUNT=8
TWO_FACTOR_MAX_VERIFY_ATTEMPTS=5
```

说明：

- `ALLOWED_ORIGINS` 支持 JSON 数组、逗号分隔字符串或单值
- `OAUTH_LIST` 支持 JSON 数组、逗号分隔字符串或单值；包含 `GITHUB` / `GOOGLE` 时启用对应 OAuth 登录
- `EXTERNAL_PROVIDER_MOCK_LIST` 控制哪些外部服务使用本地 mock target；可选值见 [providers 文档](./src/server/providers/README.md)
- `MOCK_PROVIDER_BACKEND_URL` 是 mock service 脚本持续推送 runtime config 的后端地址
- `MOCK_PROVIDER_PUBLISH_INTERVAL_SECONDS` 控制 mock service 脚本重新推送 runtime config 的间隔
- `VITE_API_BASE_URL` 默认是 `/api`，适合前后端同域部署
- `VITE_TURNSTILE_SITE_KEY` 用于在登录 / 注册页展示人机校验组件；dev mock 模式下前端会优先读取后端 runtime config
- `TURNSTILE_ENABLED` 启用后端 Turnstile 校验；默认 `false`
- `APP_DOMAIN` 用于生成对外访问链接，例如密码重置链接
- `GITHUB_*` / `GOOGLE_*` 用于第三方 OAuth App 配置，callback 默认是 `/api/oauth/{provider}/callback`
- `EXAMPLE_EXTERNAL_API_BASE_URL` 是示例外部 API real provider 的 base URL
- `TWO_FACTOR_ENCRYPTION_KEY` 用于加密存储 TOTP secret，生产环境必须覆盖
- `TWO_FACTOR_ISSUER_NAME` 会显示在 Google Authenticator、1Password 等应用中
- `TWO_FACTOR_CHALLENGE_TTL_MINUTES` 和 `TWO_FACTOR_MAX_VERIFY_ATTEMPTS` 控制两阶段登录挑战的有效期与失败阈值
- 数据库默认写入 `data/database.db`
- 初始化数据库时会按 `INIT_ADMIN_*` 自动引导默认管理员
- 开发/测试环境如果未配置邮件发送账号，验证码和重置链接会写入日志，便于本地联调

## 本地 Mock Provider

本项目的 provider mock 模式不是在后端直接返回假数据，而是启动本地 mock service。后端仍然执行真实 HTTP/SMTP 请求，只是目标地址由 dev runtime config 指向本地随机端口。

1. 在 `.env` 中启用需要 mock 的 provider：

```ini
APP_ENV=dev
EXTERNAL_PROVIDER_MOCK_LIST=["github_oauth","google_oauth","turnstile","mail","example_external_api"]
MOCK_PROVIDER_BACKEND_URL=http://localhost:8000
```

2. 启动后端和前端：

```bash
.venv/bin/python run.py
pnpm dev
```

3. 另开终端启动 mock services：

```bash
.venv/bin/python scripts/mock_provider_services.py
```

脚本会为每个 mock service 绑定随机端口，并持续调用 `POST /api/dev/providers/runtime-config` 把配置推给后端。浏览器侧配置通过 `GET /api/dev/providers/frontend-config` 从后端读取，所以不需要手动填写随机端口。

可用 mock provider：

- `github_oauth`：带确认页的 GitHub OAuth mock
- `google_oauth`：带确认页的 Google OAuth mock
- `turnstile`：提供 mock `api.js` 和 siteverify API
- `mail`：本地 SMTP mock，并提供 inbox 页面查看收到的邮件
- `example_external_api`：示例 HTTP API mock

更多细节见 [src/server/providers/README.md](./src/server/providers/README.md) 及各 provider 子目录 README。

## 2FA 流程

- 用户未开启 2FA 时，`POST /api/auth/login` 保持原行为，直接返回 access token 并设置 refresh cookie
- 用户已开启 2FA 时，`POST /api/auth/login` 返回 `202` 和一次性的 `challenge_token`
- 前端继续调用 `POST /api/auth/2fa/verify`，提交 `challenge_token + TOTP/backup code`
- 在个人中心可以完成 2FA 开启、关闭以及 backup codes 重新生成

## OAuth 流程

- `GET /api/oauth/providers` 返回当前启用的 OAuth 渠道，前端按 `GITHUB` / `GOOGLE` 显示对应登录按钮
- `GET /api/oauth/github/authorize` 发起 GitHub OAuth，`GET /api/oauth/github/callback` 处理 GitHub 回调
- `GET /api/oauth/google/authorize` 发起 Google OAuth，`GET /api/oauth/google/callback` 处理 Google 回调
- GitHub 首次登录会使用已验证主邮箱自动创建普通用户；邮箱已存在时绑定已有本地用户
- Google 首次登录会使用已验证邮箱自动创建普通用户；邮箱已存在时绑定已有本地用户
- OAuth 回调后前端通过一次性 ticket 换取本地登录态，ticket 仅可使用一次并会过期
- 已开启本地 2FA 的用户在第三方 OAuth 验证后仍需输入本地 TOTP 或 backup code

## OAuth Provider 流程

- 管理员通过 `/api/oauth-provider/clients` 管理可接入本系统的 OAuth Client
- Authorization Code + PKCE：第三方应用跳转 `/oauth/authorize`，确认后用 `POST /api/oauth-provider/token` 换取 token
- Device Code Flow：设备端调用 `POST /api/oauth-provider/device_authorization` 获取 `device_code/user_code`
- 用户在 `verification_uri` 或 `/oauth/device` 输入 `user_code` 并确认授权
- 设备端轮询 `POST /api/oauth-provider/token`，`grant_type` 使用 `urn:ietf:params:oauth:grant-type:device_code`

## 开发说明

### 后端

本地启动：

```bash
.venv/bin/python run.py
```

或者：

```bash
.venv/bin/python -m uvicorn src.server.main:app --reload --port 8000
```

后端会在启动时：

- 加载 `.env` 与 `.env.{APP_ENV}`
- 初始化日志配置
- 检查数据库是否存在，不存在时自动初始化
- 如果 `dist/` 存在，则在根路径挂载前端 SPA

### 前端

```bash
pnpm dev
pnpm build
pnpm preview
pnpm lint
```

前端通过 [`src/client/lib/api.ts`](/home/jese--ki/Projects/dev/fullstack-template/src/client/lib/api.ts) 中的 Axios 实例访问后端，默认基地址为 `/api`。

### 数据库工具

```bash
.venv/bin/python scripts/init_db.py
.venv/bin/python scripts/init_db.py --check
.venv/bin/python scripts/init_db.py --reset
```

## 质量检查与测试

后端测试请使用仓库约定命令：

```bash
.venv/bin/python -m pytest . -q
```

常用检查：

```bash
pnpm lint
.venv/bin/ruff check --fix
.venv/bin/mypy .
```

也可以直接执行：

```bash
make check
```

## 生产构建与部署

### 构建前端并由后端托管

```bash
pnpm build
.venv/bin/python run.py
```

构建完成后，后端会从 `dist/` 提供前端静态资源，并对非 `/api` 路径执行 SPA 回退。

### Docker

```bash
docker compose up -d --build
```

当前容器行为：

- 构建阶段执行前端打包
- 运行阶段执行 `alembic upgrade head`
- 启动时确保 `/app/data` 存在
- 最终以 `python run.py` 提供 API 和前端页面

`docker-compose.yml` 默认挂载：

- `./data:/app/data`
- `./logs:/app/logs`

## 相关接口文档

- 认证模块文档：[src/server/auth/README.md](./src/server/auth/README.md)
- 示例模块文档：[src/server/example_module/README.md](./src/server/example_module/README.md)
- 外部 Provider 文档：[src/server/providers/README.md](./src/server/providers/README.md)

可直接试用：

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/example/ping
```

## 开发约定

- 路由层负责参数校验与编排
- 业务逻辑放在 service 层
- 数据访问下沉到 DAO 层
- 新增模块时，需要在数据库初始化过程中导入模型，并在 `main.py` 中挂载 router
- 测试环境下数据库会被重建，以保证测试隔离

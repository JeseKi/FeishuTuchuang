# Feishu Image Host

Feishu Image Host 是一个自托管飞书图床。图片上传到飞书 Drive，本机磁盘作为热缓存，对外提供稳定的图片访问 URL。

## 功能

- 飞书 Drive 冷存储：通过飞书用户 OAuth 授权上传、下载、删除和移动图片。
- 本地热缓存：公开访问 `/i/{filename}` 时优先命中本地缓存，缺失时从飞书回源。
- 图片管理台：上传图片、筛选历史、预览、复制 URL、管理飞书目标文件夹。
- API Key 集成：支持 `/api/v1/images` 和 `/api/v2/images` 给外部工具上传图片。
- 自托管账号：管理员引导、登录、刷新令牌、个人资料、密码修改、TOTP 2FA、设备管理。
- SQLite + Alembic：默认写入 `data/database.db`，容器启动会执行迁移并备份现有数据库。

## 快速入口

- [Docker Compose 部署](guide/deployment.md)
- [首次初始化](guide/initialization.md)
- [环境变量配置](guide/configuration.md)
- [飞书应用配置](guide/feishu-app.md)
- [API Key 使用](guide/api-key.md)
- [内置文档站点](guide/embedded-docs.md)

## 默认部署形态

默认形态适合个人和小团队部署：公开注册关闭，由管理员创建用户；旧全栈模板时期的示例模块、OAuth Provider、Scope 管理和开发 Provider Runtime 代码仍保留，但默认不挂载路由、不显示入口。

生产环境建议：

- 使用 Docker Compose 部署应用。
- 使用 Nginx、Caddy 或 Traefik 在应用前面提供 HTTPS。
- 使用专门的飞书 Drive 文件夹存放图床文件。
- 定期备份 `data/`、`logs/` 和 `.env`。

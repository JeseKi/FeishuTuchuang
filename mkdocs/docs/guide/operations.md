# 运维

## 查看日志

```bash
docker compose logs -f app
```

## 重启服务

```bash
docker compose restart app
```

## 更新代码并重新构建

```bash
git pull
docker compose up -d --build
```

## 备份数据

```bash
tar czf feishu-image-host-data-$(date +%F).tar.gz data logs .env
```

需要备份的内容：

- `data/`：SQLite 数据库和图片缓存。
- `logs/`：应用日志。
- `.env`：部署配置和密钥。

## 恢复数据

把 `data/`、`logs/` 和 `.env` 放回项目目录，再执行：

```bash
docker compose up -d --build
```

## 数据库迁移

容器启动时会自动检查并执行 Alembic 迁移。

如果检测到旧数据库已有表但缺少 Alembic 版本记录，启动脚本会先标记基线版本，再执行迁移。

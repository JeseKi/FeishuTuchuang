# 内置文档

内置文档用于在容器中直接托管 MkDocs 构建产物，适合私有部署时把使用说明和服务放在同一个域名下。

## 启用方式

默认关闭。需要启用时，在 `.env` 中设置：

```ini
ENABLE_DOCS=true
```

然后重新构建镜像：

```bash
docker compose up -d --build
```

访问地址：

```text
https://img.example.com/mkdocs/docs/
```

## 构建方式

文档静态站点在 Docker image build 阶段通过 `mkdocs build --strict` 生成。运行时只根据 `ENABLE_DOCS` 决定是否挂载，不会临时构建文档。

这样可以避免：

- 容器启动变慢。
- MkDocs 依赖污染后端运行依赖。
- 文档构建失败到运行时才暴露。

## 路由行为

启用后，后端会把 MkDocs 静态站点挂载到：

```text
/mkdocs/docs/
```

关闭时，该路径返回 404，不会被前端 SPA fallback 成首页。

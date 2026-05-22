# 本地开发

## 后端测试

```bash
.venv/bin/python -m pytest . -q
```

## 后端本地启动

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/python run.py
```

默认后端地址：

```text
http://localhost:8000
```

健康检查：

```text
http://localhost:8000/api/health
```

## 前端开发

```bash
pnpm install
pnpm dev
```

默认前端开发服务器：

```text
http://localhost:5173
```

## 文档预览

文档依赖独立放在 `mkdocs/requirements.txt`。

```bash
uv pip install -r mkdocs/requirements.txt
mkdocs serve
```

默认访问：

```text
http://127.0.0.1:8000
```

## 完整检查

```bash
.venv/bin/python -m pytest . -q
pnpm lint
pnpm build
mkdocs build --strict
```

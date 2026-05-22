FROM node:23-alpine AS builder
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && corepack install
RUN pnpm install --frozen-lockfile
COPY . .
COPY .env .
RUN pnpm run build

FROM python:3.11-slim AS docs-builder
WORKDIR /app
COPY mkdocs.yml .
COPY mkdocs/requirements.txt ./mkdocs/requirements.txt
COPY mkdocs/docs ./mkdocs/docs
RUN pip install uv
RUN uv pip install --no-cache-dir -r mkdocs/requirements.txt --system
RUN mkdocs build --strict

FROM python:3.11-slim
WORKDIR /app
COPY .env .
COPY requirements.txt .
RUN pip install uv
RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY src/server/ ./src/server/
COPY --from=builder /app/dist ./dist
COPY --from=docs-builder /app/mkdocs/site ./mkdocs/site
COPY run.py .
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]

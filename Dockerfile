FROM node:23-alpine AS builder
WORKDIR /app
ARG MIRROR_MODE=auto

COPY package.json pnpm-lock.yaml* ./
RUN set -eux; \
    mirror_mode="$MIRROR_MODE"; \
    if [ "$mirror_mode" = "auto" ]; then \
        if node -e "const c = new AbortController(); setTimeout(() => c.abort(), 3000); fetch('https://www.google.com/generate_204', { signal: c.signal }).then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1));"; then \
            mirror_mode="global"; \
        else \
            mirror_mode="cn"; \
        fi; \
    fi; \
    case "$mirror_mode" in \
        cn) \
            sed -i 's#https://dl-cdn.alpinelinux.org/alpine#https://mirrors.tuna.tsinghua.edu.cn/alpine#g' /etc/apk/repositories; \
            npm_registry="https://registry.npmmirror.com"; \
            ;; \
        global) \
            npm_registry="https://registry.npmjs.org"; \
            ;; \
        *) \
            echo "Unsupported MIRROR_MODE: $MIRROR_MODE"; \
            exit 1; \
            ;; \
    esac; \
    echo "Using mirror mode: $mirror_mode"; \
    npm config set registry "$npm_registry"; \
    COREPACK_NPM_REGISTRY="$npm_registry" corepack enable; \
    COREPACK_NPM_REGISTRY="$npm_registry" corepack install
RUN pnpm install --frozen-lockfile
COPY . .
COPY .env .
RUN pnpm run build

FROM python:3.11-slim AS docs-builder
WORKDIR /app
ARG MIRROR_MODE=auto
COPY mkdocs.yml .
COPY mkdocs/requirements.txt ./mkdocs/requirements.txt
COPY mkdocs/docs ./mkdocs/docs
RUN set -eux; \
    mirror_mode="$MIRROR_MODE"; \
    if [ "$mirror_mode" = "auto" ]; then \
        if python -c "import urllib.request; urllib.request.urlopen('https://www.google.com/generate_204', timeout=3).close()"; then \
            mirror_mode="global"; \
        else \
            mirror_mode="cn"; \
        fi; \
    fi; \
    case "$mirror_mode" in \
        cn) \
            . /etc/os-release; \
            printf 'Types: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian\nSuites: %s %s-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\nTypes: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security\nSuites: %s-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n' "$VERSION_CODENAME" "$VERSION_CODENAME" "$VERSION_CODENAME" > /etc/apt/sources.list.d/debian.sources; \
            pypi_index="https://pypi.tuna.tsinghua.edu.cn/simple"; \
            ;; \
        global) \
            pypi_index="https://pypi.org/simple"; \
            ;; \
        *) \
            echo "Unsupported MIRROR_MODE: $MIRROR_MODE"; \
            exit 1; \
            ;; \
    esac; \
    echo "Using mirror mode: $mirror_mode"; \
    pip install --no-cache-dir --index-url "$pypi_index" uv; \
    uv pip install --no-cache-dir --index-url "$pypi_index" -r mkdocs/requirements.txt --system
RUN mkdocs build --strict

FROM python:3.11-slim
WORKDIR /app
ARG MIRROR_MODE=auto
COPY .env .
COPY requirements.txt .
RUN set -eux; \
    mirror_mode="$MIRROR_MODE"; \
    if [ "$mirror_mode" = "auto" ]; then \
        if python -c "import urllib.request; urllib.request.urlopen('https://www.google.com/generate_204', timeout=3).close()"; then \
            mirror_mode="global"; \
        else \
            mirror_mode="cn"; \
        fi; \
    fi; \
    case "$mirror_mode" in \
        cn) \
            . /etc/os-release; \
            printf 'Types: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian\nSuites: %s %s-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\nTypes: deb\nURIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security\nSuites: %s-security\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n' "$VERSION_CODENAME" "$VERSION_CODENAME" "$VERSION_CODENAME" > /etc/apt/sources.list.d/debian.sources; \
            pypi_index="https://pypi.tuna.tsinghua.edu.cn/simple"; \
            ;; \
        global) \
            pypi_index="https://pypi.org/simple"; \
            ;; \
        *) \
            echo "Unsupported MIRROR_MODE: $MIRROR_MODE"; \
            exit 1; \
            ;; \
    esac; \
    echo "Using mirror mode: $mirror_mode"; \
    pip install --no-cache-dir --index-url "$pypi_index" uv; \
    uv pip install --no-cache-dir --index-url "$pypi_index" -r requirements.txt --system

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

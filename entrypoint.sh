#!/bin/sh
set -e

DB_PATH="/app/data/database.db"
BACKUP_PATH="${DB_PATH}.bak"

backup_database() {
    if [ ! -f "$DB_PATH" ]; then
        echo "未找到现有数据库，跳过备份"
        return 0
    fi

    echo "开始备份数据库..."
    rm -f "${BACKUP_PATH}.3"

    if [ -f "${BACKUP_PATH}.2" ]; then
        mv "${BACKUP_PATH}.2" "${BACKUP_PATH}.3"
    fi

    if [ -f "${BACKUP_PATH}.1" ]; then
        mv "${BACKUP_PATH}.1" "${BACKUP_PATH}.2"
    fi

    if [ -f "$BACKUP_PATH" ]; then
        mv "$BACKUP_PATH" "${BACKUP_PATH}.1"
    fi

    cp "$DB_PATH" "$BACKUP_PATH"
    echo "数据库备份完成: ${BACKUP_PATH}"
}

stamp_legacy_database_if_needed() {
    if [ ! -f "$DB_PATH" ]; then
        return 0
    fi

    LEGACY_REVISION="$(DB_PATH="$DB_PATH" python - <<'PY'
import os
import sqlite3

db_path = os.environ["DB_PATH"]

conn = sqlite3.connect(db_path)
try:
    cur = conn.cursor()
    tables = {
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    if "alembic_version" in tables:
        versions = list(cur.execute("SELECT version_num FROM alembic_version"))
        if versions:
            print("")
            raise SystemExit(0)

    if "image_host_assets" not in tables:
        print("")
        raise SystemExit(0)

    columns = {
        row[1]: row
        for row in cur.execute("PRAGMA table_info(image_host_assets)")
    }

    if "api_keys" in tables:
        print("20260511_0006")
    elif "image_host_feishu_oauth_tokens" in tables:
        feishu_image_key = columns.get("feishu_image_key")
        if feishu_image_key is None or int(feishu_image_key[3]) == 0:
            print("20260511_0005")
        else:
            print("20260511_0004")
    elif "feishu_file_token" in columns:
        print("20260511_0003")
    elif "last_accessed_at" in columns:
        print("20260511_0002")
    else:
        print("20260511_0001")
finally:
    conn.close()
PY
)"

    if [ -n "$LEGACY_REVISION" ]; then
        echo "检测到已有表但缺少 Alembic 版本记录，标记基线: ${LEGACY_REVISION}"
        alembic stamp "$LEGACY_REVISION"
    fi
}

# 确保 data 目录存在（volume 挂载时可能为空）
mkdir -p /app/data

backup_database

# 运行数据库迁移

if [ ! -f "$DB_PATH" ]; then
    echo "未找到现有数据库，跳过迁移"

else
    stamp_legacy_database_if_needed
    echo "正在运行数据库迁移..."
    alembic upgrade head
    echo "数据库迁移完成"
fi

# 启动应用
exec python run.py

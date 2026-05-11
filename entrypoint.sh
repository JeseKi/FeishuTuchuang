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

# 确保 data 目录存在（volume 挂载时可能为空）
mkdir -p /app/data

backup_database

# 运行数据库迁移

if [ ! -f "$DB_PATH" ]; then
    echo "未找到现有数据库，跳过迁移"

else
    echo "正在运行数据库迁移..."
    alembic upgrade head
    echo "数据库迁移完成"
fi

# 启动应用
exec python run.py

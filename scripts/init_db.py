#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化/检查模板数据库的 CLI

用法：
- python -m scripts.initdb --check   # 检查表
- python -m scripts.initdb --reset   # 重置并初始化
- python -m scripts.initdb           # 仅初始化（若不存在）
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger

from src.server.database import init_database, get_database_info, engine


def reset_database() -> None:
    """删除数据库文件并重新初始化。仅用于开发。"""
    info = get_database_info()
    db_path = Path(info.database_path)
    try:
        engine.dispose()
    except Exception:
        pass
    if db_path.exists():
        db_path.unlink()
        logger.info("已删除数据库文件：{}", db_path)
    init_database()


def check_status() -> None:
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info("当前数据库表: {}", tables)


def main() -> None:
    parser = argparse.ArgumentParser(description="模板数据库工具")
    parser.add_argument(
        "--reset", action="store_true", help="重置数据库（删除后再初始化）"
    )
    parser.add_argument("--check", action="store_true", help="检查数据库状态")
    args = parser.parse_args()

    if args.check:
        check_status()
        return
    if args.reset:
        reset_database()
        return

    # 默认：仅初始化（幂等）
    init_database()


if __name__ == "__main__":
    main()

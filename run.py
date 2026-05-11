#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地便捷启动脚本

公开接口：
- 直接运行该脚本启动 uvicorn

内部方法：
- 无
"""

import uvicorn
import os
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger

from src.server.logging_config import setup_logging

if __name__ == "__main__":
    load_dotenv(Path.cwd() / ".env")
    setup_logging()
    logger.info("Fullstack Template 启动！")
    logger.info(f"当前应用环境：{os.getenv('APP_ENV')}")

    uvicorn.run(
        "src.server.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=False,
        log_config=None,
    )

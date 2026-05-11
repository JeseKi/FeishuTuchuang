# -*- coding: utf-8 -*-
"""
Loguru 日志初始化。

职责：
- 统一初始化控制台和本地文件日志
- 将标准 logging 转发到 Loguru
- 提供 app/access/error 三类日志输出
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from types import FrameType

import loguru
from loguru import logger

from src.server.config import global_config

_LOGGING_CONFIGURED = False

DEFAULT_LOG_EXTRA = {
    "log_type": "app",
    "request_id": "-",
    "client_ip": "-",
    "user_id": "-",
}

COMMON_LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level:<8} | "
    "rid={extra[request_id]} | "
    "ip={extra[client_ip]} | "
    "uid={extra[user_id]} | "
    "{name}:{function}:{line} | "
    "{message}"
)


class InterceptHandler(logging.Handler):
    """将标准库 logging 记录转发到 Loguru。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(log_type="app").opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def _resolve_log_dir() -> Path:
    return global_config.project_root / global_config.log_dir


def _is_access_log(record: loguru.Record) -> bool:
    return record["extra"].get("log_type") == "access"


def _is_app_log(record: loguru.Record) -> bool:
    return record["extra"].get("log_type", "app") != "access"


def _is_error_log(record: loguru.Record) -> bool:
    return record["level"].no >= logging.ERROR


def _configure_standard_logging() -> None:
    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [intercept_handler]
        std_logger.propagate = False


def setup_logging() -> None:
    """初始化全局日志配置。"""

    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    log_dir = _resolve_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    use_enqueue = global_config.app_env != "test" and not os.getenv(
        "PYTEST_CURRENT_TEST"
    )

    logger.remove()
    logger.configure(extra=DEFAULT_LOG_EXTRA)

    logger.add(
        sys.stdout,
        level=global_config.log_level.upper(),
        format=COMMON_LOG_FORMAT,
        colorize=False,
        enqueue=use_enqueue,
        backtrace=True,
        diagnose=global_config.app_env == "dev",
    )
    logger.add(
        log_dir / "app.log",
        level=global_config.log_level.upper(),
        format=COMMON_LOG_FORMAT,
        filter=_is_app_log,
        rotation=global_config.log_rotation,
        retention=global_config.log_retention,
        serialize=global_config.log_serialize,
        encoding="utf-8",
        enqueue=use_enqueue,
        backtrace=True,
        diagnose=global_config.app_env == "dev",
    )
    logger.add(
        log_dir / "access.log",
        level="INFO",
        format=COMMON_LOG_FORMAT,
        filter=_is_access_log,
        rotation=global_config.log_rotation,
        retention=global_config.log_retention,
        serialize=global_config.log_serialize,
        encoding="utf-8",
        enqueue=use_enqueue,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        format=COMMON_LOG_FORMAT,
        filter=_is_error_log,
        rotation=global_config.log_rotation,
        retention=global_config.log_retention,
        serialize=global_config.log_serialize,
        encoding="utf-8",
        enqueue=use_enqueue,
        backtrace=True,
        diagnose=global_config.app_env == "dev",
    )

    _configure_standard_logging()
    _LOGGING_CONFIGURED = True

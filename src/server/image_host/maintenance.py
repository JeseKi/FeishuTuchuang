# -*- coding: utf-8 -*-
"""图床缓存维护任务。"""

from __future__ import annotations

import asyncio
from contextlib import suppress

from loguru import logger

from .config import image_host_config
from .oauth import refresh_oauth_token_if_needed
from .service import cleanup_expired_cache_files, flush_pending_image_accesses


async def run_once() -> None:
    from src.server.database import SessionLocal

    db = SessionLocal()
    try:
        flushed_count = flush_pending_image_accesses(db)
        deleted_count = cleanup_expired_cache_files(db)
        refreshed_oauth = await refresh_oauth_token_if_needed()
        if flushed_count or deleted_count or refreshed_oauth:
            logger.info(
                f"图床缓存维护完成：访问时间落库 {flushed_count} 条，"
                f"清理本地缓存 {deleted_count} 个文件，"
                f"飞书 OAuth 刷新 {'是' if refreshed_oauth else '否'}。"
            )
    except Exception:
        logger.exception("图床缓存维护失败")
    finally:
        db.close()


async def maintenance_loop() -> None:
    while True:
        await asyncio.sleep(image_host_config.access_flush_interval_seconds)
        await run_once()


def start_maintenance_task() -> asyncio.Task[None]:
    return asyncio.create_task(maintenance_loop(), name="image-host-cache-maintenance")


async def stop_maintenance_task(task: asyncio.Task[None] | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await run_once()

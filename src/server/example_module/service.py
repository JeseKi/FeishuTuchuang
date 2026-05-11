# -*- coding: utf-8 -*-
"""
示例模块服务层（模板版）

公开接口：
- create_item(db, name)
- get_item(db, item_id)

内部方法：
- 无

说明：
- 服务层承载业务逻辑，路由层只做参数校验与装配。
"""

from __future__ import annotations

import os
import secrets
import string
from datetime import datetime, timezone
from threading import Thread
from time import sleep

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.server.auth.models import User
from src.server.providers import get_example_external_api_provider
from .dao import ExampleAsyncTaskDAO, ExampleItemDAO

from .models import ExampleAsyncTask, ExampleAsyncTaskLog, Item
from .schemas import AsyncTaskCreate

ASYNC_TASK_ID_LENGTH = 32
ASYNC_TASK_ID_ALPHABET = string.ascii_letters + string.digits
MAX_TASK_ID_GENERATION_ATTEMPTS = 5


def create_item(db: Session, name: str) -> Item:
    dao = ExampleItemDAO(db)
    try:
        return dao.create(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="名称已存在"
        )


def get_item(db: Session, item_id: int) -> Item:
    dao = ExampleItemDAO(db)
    item = dao.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到")
    return item


async def fetch_external_status():
    return await get_example_external_api_provider().fetch_status()


def create_async_task(
    db: Session, payload: AsyncTaskCreate, current_user: User
) -> ExampleAsyncTask:
    task_name = payload.name.strip()
    if not task_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="任务名称不能为空"
        )

    task_dao = ExampleAsyncTaskDAO(db)
    task = None
    for _ in range(MAX_TASK_ID_GENERATION_ATTEMPTS):
        task_id = _generate_async_task_id()
        if task_dao.get(task_id):
            continue

        try:
            task = task_dao.create(
                task_id=task_id,
                name=task_name,
                total_count=payload.total_count,
                fail_every=payload.fail_every,
                delay_ms=payload.delay_ms,
                requested_by_user_id=current_user.id,
            )
            break
        except IntegrityError:
            db.rollback()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务ID生成失败，请重试",
        )

    task_dao.append_log(
        task.id,
        level="info",
        message=f"任务已创建，总计 {payload.total_count} 项待处理。",
    )
    return task


def get_async_task_detail(
    db: Session, task_id: str
) -> tuple[ExampleAsyncTask, list[ExampleAsyncTaskLog]]:
    task_dao = ExampleAsyncTaskDAO(db)
    task = task_dao.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    logs = task_dao.list_logs(task_id)
    return task, logs


def launch_async_task(db: Session, task_id: str) -> None:
    session_factory = _build_session_factory(db)
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("APP_ENV") == "test":
        _run_async_task(session_factory, task_id)
        return

    worker = Thread(
        target=_run_async_task,
        args=(session_factory, task_id),
        daemon=True,
        name=f"example-task-{task_id}",
    )
    worker.start()


def _build_session_factory(db: Session) -> sessionmaker[Session]:
    bind = db.get_bind()
    if isinstance(bind, Connection):
        bind = bind.engine
    if not isinstance(bind, Engine):
        raise RuntimeError("无法创建任务会话工厂")
    return sessionmaker(bind=bind, autocommit=False, autoflush=False)


def _run_async_task(session_factory: sessionmaker[Session], task_id: str) -> None:
    db = session_factory()
    task_dao = ExampleAsyncTaskDAO(db)
    processed_count = 0
    success_count = 0
    failure_count = 0

    try:
        task = task_dao.get(task_id)
        if not task:
            return

        task_dao.update_status(
            task_id,
            status="running",
            last_message="任务开始执行",
            started_at=datetime.now(timezone.utc),
        )
        task_dao.append_log(
            task_id,
            level="info",
            message=f"任务启动，预计处理 {task.total_count} 项数据。",
        )

        for index in range(1, task.total_count + 1):
            if task.delay_ms > 0:
                sleep(task.delay_ms / 1000)

            if task.fail_every > 0 and index % task.fail_every == 0:
                failure_count += 1
                level = "warning"
                detail = f"第 {index} 项处理失败（模拟失败样本）"
            else:
                success_count += 1
                level = "info"
                detail = f"第 {index} 项处理成功"

            processed_count = success_count + failure_count
            task_dao.update_progress(
                task_id,
                processed_count=processed_count,
                success_count=success_count,
                failure_count=failure_count,
                last_message=detail,
            )
            task_dao.append_log(task_id, level=level, message=detail)

        summary = (
            f"任务执行完成，成功 {success_count} 项，失败 {failure_count} 项。"
        )
        task_dao.mark_completed(
            task_id,
            processed_count=processed_count,
            success_count=success_count,
            failure_count=failure_count,
            last_message=summary,
        )
        task_dao.append_log(task_id, level="info", message=summary)
    except Exception as exc:
        error_message = f"任务执行异常：{exc}"
        task_dao.mark_failed(
            task_id,
            processed_count=processed_count,
            success_count=success_count,
            failure_count=failure_count,
            last_message=error_message,
        )
        task_dao.append_log(task_id, level="error", message=error_message)
    finally:
        db.close()


def _generate_async_task_id() -> str:
    return "".join(
        secrets.choice(ASYNC_TASK_ID_ALPHABET)
        for _ in range(ASYNC_TASK_ID_LENGTH)
    )

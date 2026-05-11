# -*- coding: utf-8 -*-
"""
示例模块 DAO（可选示范）

公开接口：
- `ExampleItemDAO`
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from .models import ExampleAsyncTask, ExampleAsyncTaskLog, Item


class ExampleItemDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, name: str) -> Item:
        exists = self.db_session.query(Item).filter(Item.name == name).first()
        if exists:
            raise ValueError("名称已存在")
        item = Item(name=name)
        self.db_session.add(item)
        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def get(self, item_id: int) -> Item | None:
        return self.db_session.query(Item).filter(Item.id == item_id).first()


class ExampleAsyncTaskDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(
        self,
        *,
        task_id: str,
        name: str,
        total_count: int,
        fail_every: int,
        delay_ms: int,
        requested_by_user_id: int | None,
    ) -> ExampleAsyncTask:
        task = ExampleAsyncTask(
            id=task_id,
            name=name,
            status="pending",
            total_count=total_count,
            processed_count=0,
            success_count=0,
            failure_count=0,
            progress_percent=0,
            fail_every=fail_every,
            delay_ms=delay_ms,
            last_message="任务已创建，等待执行",
            requested_by_user_id=requested_by_user_id,
        )
        self.db_session.add(task)
        self.db_session.commit()
        self.db_session.refresh(task)
        return task

    def get(self, task_id: str) -> ExampleAsyncTask | None:
        return (
            self.db_session.query(ExampleAsyncTask)
            .populate_existing()
            .filter(ExampleAsyncTask.id == task_id)
            .first()
        )

    def list_logs(self, task_id: str) -> list[ExampleAsyncTaskLog]:
        return (
            self.db_session.query(ExampleAsyncTaskLog)
            .filter(ExampleAsyncTaskLog.task_id == task_id)
            .order_by(ExampleAsyncTaskLog.sequence.asc(), ExampleAsyncTaskLog.id.asc())
            .all()
        )

    def append_log(
        self, task_id: str, *, level: str, message: str
    ) -> ExampleAsyncTaskLog:
        current_max = (
            self.db_session.query(func.max(ExampleAsyncTaskLog.sequence))
            .filter(ExampleAsyncTaskLog.task_id == task_id)
            .scalar()
        )
        next_sequence = (current_max or 0) + 1
        log = ExampleAsyncTaskLog(
            task_id=task_id,
            sequence=next_sequence,
            level=level,
            message=message,
        )
        self.db_session.add(log)
        self.db_session.commit()
        self.db_session.refresh(log)
        return log

    def update_status(
        self,
        task_id: str,
        *,
        status: str,
        last_message: str,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> ExampleAsyncTask:
        task = self.get(task_id)
        if not task:
            raise ValueError("任务不存在")
        task.status = status
        task.last_message = last_message
        if started_at is not None:
            task.started_at = started_at
        if finished_at is not None:
            task.finished_at = finished_at
        self.db_session.commit()
        self.db_session.refresh(task)
        return task

    def update_progress(
        self,
        task_id: str,
        *,
        processed_count: int,
        success_count: int,
        failure_count: int,
        last_message: str,
    ) -> ExampleAsyncTask:
        task = self.get(task_id)
        if not task:
            raise ValueError("任务不存在")
        task.processed_count = processed_count
        task.success_count = success_count
        task.failure_count = failure_count
        task.progress_percent = int(processed_count * 100 / max(task.total_count, 1))
        task.last_message = last_message
        self.db_session.commit()
        self.db_session.refresh(task)
        return task

    def mark_completed(
        self,
        task_id: str,
        *,
        processed_count: int,
        success_count: int,
        failure_count: int,
        last_message: str,
    ) -> ExampleAsyncTask:
        task = self.get(task_id)
        if not task:
            raise ValueError("任务不存在")
        task.status = "completed"
        task.processed_count = processed_count
        task.success_count = success_count
        task.failure_count = failure_count
        task.progress_percent = 100
        task.last_message = last_message
        task.finished_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(task)
        return task

    def mark_failed(
        self,
        task_id: str,
        *,
        processed_count: int,
        success_count: int,
        failure_count: int,
        last_message: str,
    ) -> ExampleAsyncTask:
        task = self.get(task_id)
        if not task:
            raise ValueError("任务不存在")
        task.status = "failed"
        task.processed_count = processed_count
        task.success_count = success_count
        task.failure_count = failure_count
        task.progress_percent = int(processed_count * 100 / max(task.total_count, 1))
        task.last_message = last_message
        task.finished_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(task)
        return task

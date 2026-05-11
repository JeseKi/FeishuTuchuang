# -*- coding: utf-8 -*-
"""
示例模块DAO层测试
"""

import pytest
from sqlalchemy.orm import Session

from src.server.example_module.dao import ExampleAsyncTaskDAO, ExampleItemDAO
from src.server.example_module.models import Item


def test_example_item_dao_create(test_db_session: Session):
    """测试创建项目"""
    dao = ExampleItemDAO(test_db_session)

    # 正常创建
    item = dao.create("test_item")

    assert item is not None
    assert item.name == "test_item"

    # 测试重复名称
    with pytest.raises(ValueError) as exc_info:
        dao.create("test_item")

    assert str(exc_info.value) == "名称已存在"


def test_example_item_dao_get(test_db_session: Session):
    """测试获取项目"""
    # 准备测试数据
    item = Item(name="test_item")
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    dao = ExampleItemDAO(test_db_session)

    # 获取存在的项目
    retrieved_item = dao.get(item.id)
    assert retrieved_item is not None
    assert retrieved_item.id == item.id
    assert retrieved_item.name == "test_item"

    # 获取不存在的项目
    retrieved_item = dao.get(999999)
    assert retrieved_item is None


def test_example_async_task_dao_flow(test_db_session: Session):
    dao = ExampleAsyncTaskDAO(test_db_session)
    task_id = "A" * 32

    task = dao.create(
        task_id=task_id,
        name="batch-job",
        total_count=6,
        fail_every=2,
        delay_ms=50,
        requested_by_user_id=1,
    )

    assert task.status == "pending"
    assert task.id == task_id
    assert task.progress_percent == 0
    assert task.total_count == 6

    dao.append_log(task.id, level="info", message="任务已创建")
    dao.update_status(task.id, status="running", last_message="任务执行中")
    dao.update_progress(
        task.id,
        processed_count=3,
        success_count=2,
        failure_count=1,
        last_message="第 3 项处理成功",
    )
    completed = dao.mark_completed(
        task.id,
        processed_count=6,
        success_count=3,
        failure_count=3,
        last_message="任务执行完成",
    )

    logs = dao.list_logs(task.id)

    assert completed.status == "completed"
    assert completed.processed_count == 6
    assert completed.success_count == 3
    assert completed.failure_count == 3
    assert completed.progress_percent == 100
    assert completed.finished_at is not None
    assert len(logs) == 1
    assert logs[0].sequence == 1
    assert logs[0].message == "任务已创建"

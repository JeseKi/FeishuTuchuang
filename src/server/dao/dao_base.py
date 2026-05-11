# -*- coding: utf-8 -*-
"""
数据库访问对象（DAO）基类与线程池工具（模板版）

公开接口：
- `BaseDAO`：DAO 基类，持有 `db_session`
- `run_in_thread`：将同步函数放入线程池执行

内部方法：
- 无

说明：
- 用于在服务或路由中将阻塞型 ORM 调用切换至线程池，避免阻塞事件循环。
"""

import asyncio
import os
from typing import Any, Callable
from sqlalchemy.orm import Session


class BaseDAO:
    """DAO 基类"""

    def __init__(self, db_session: Session):
        self.db_session = db_session


async def run_in_thread(sync_func: Callable[[], Any]) -> Any:
    """将同步函数放到默认线程池中执行并返回结果。"""
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("APP_ENV") == "test":
        return sync_func()
    return await asyncio.to_thread(sync_func)

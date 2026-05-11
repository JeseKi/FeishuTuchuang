# -*- coding: utf-8 -*-
"""
全局通用 Pydantic 模型

公开接口：
- `DatabaseInfo`：数据库信息模型

内部方法：
- 无

说明：
- 跨模块轻量共享的数据模型放在此处
"""

from pydantic import BaseModel
from typing import Optional


class DatabaseInfo(BaseModel):
    """数据库信息模型"""

    database_exists: bool
    database_size: Optional[int] = None
    database_path: str

对于 python 测试，你需要以 `.venv/bin/python -m pytest . -q` 这样的格式来跑测试。
后端实际开发和文件分布应当参考 src/server/example_module。
如果需要补全数据库中可能缺失的字段，应当优先编写 alembic 的数据库迁移脚本，而非在代码中进行硬性的 ensure。
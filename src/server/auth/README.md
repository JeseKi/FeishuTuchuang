# 模块：auth（模板版）

## 公开接口
- POST `/api/auth/register`
- POST `/api/auth/login`
- POST `/api/auth/refresh`
- GET `/api/auth/profile`
- PUT `/api/auth/profile`
- PUT `/api/auth/password`

## 业务定位
- 提供最小可用的账号体系，支持注册、登录、个人信息、改密。开发/测试环境支持 `test_token` 便捷调试。

## 数据流
- 路由 -> 依赖注入 `get_db` -> Service -> SQLAlchemy（线程池调用在模板演示中可直接使用 `asyncio.to_thread`，本模块操作较少可直接同步）。

## 用法示例（curl）
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"Password123"}'

curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"Password123"}'
```

# 模块：auth

## 公开接口
- POST `/api/auth/login`
- POST `/api/auth/refresh`
- GET `/api/auth/profile`
- PUT `/api/auth/profile`
- PUT `/api/auth/password`
- POST `/api/auth/register`（默认关闭公开注册）

## 业务定位
- 提供自托管图床所需账号体系，支持登录、个人信息、改密、2FA 和设备管理。
- 公开注册默认关闭，建议由管理员创建用户。

## 数据流
- 路由 -> 依赖注入 `get_db` -> Service -> SQLAlchemy。

## 用法示例（curl）
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"Password123"}'
```

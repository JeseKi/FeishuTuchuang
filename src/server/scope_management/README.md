# 模块：scope_management

## 公开接口
- GET `/api/admin/scopes`
- PATCH `/api/admin/scopes/{scope_name}`

## 业务定位
- 管理系统内已知鉴权 scope 的分类。
- 分类固定为 `normal`（普通）、`sensitive`（敏感）与 `dangerous`（危险）。

## 数据流
- 路由 -> 管理员鉴权 -> 服务层同步内置 scope -> DAO -> SQLAlchemy -> SQLite

## 规范说明
- scope 名称来源于鉴权模块内的 `OAUTH2_SCOPES`，本模块只维护它们的分类信息。
- 当代码中新增内置 scope 时，列表接口会自动补齐数据库记录。
